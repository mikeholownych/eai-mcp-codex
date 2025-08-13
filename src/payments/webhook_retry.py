"""Webhook retry service for handling failed webhook deliveries."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import WebhookEvent
from .utils import verify_webhook_signature, parse_webhook_payload

logger = logging.getLogger(__name__)


class WebhookStatus(Enum):
    """Webhook processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass
class WebhookRetryConfig:
    """Configuration for webhook retry behavior."""
    max_retries: int = 5
    initial_delay: float = 1.0  # seconds
    max_delay: float = 300.0  # 5 minutes
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1
    dead_letter_threshold: int = 5


class WebhookRetryService:
    """Service for handling webhook retries and dead letter queue."""
    
    def __init__(
        self,
        db: Session,
        config: Optional[WebhookRetryConfig] = None,
        webhook_processor: Optional[Callable] = None
    ):
        self.db = db
        self.config = config or WebhookRetryConfig()
        self.webhook_processor = webhook_processor
        self.retry_queue: List[WebhookEvent] = []
        self.processing = False
    
    async def process_failed_webhooks(self):
        """Process all failed webhooks that need retrying."""
        if self.processing:
            logger.warning("Webhook processing already in progress")
            return
        
        self.processing = True
        
        try:
            # Get failed webhooks that need retrying
            failed_webhooks = self.db.query(WebhookEvent).filter(
                and_(
                    WebhookEvent.processing_status.in_([WebhookStatus.FAILED.value, WebhookStatus.RETRYING.value]),
                    WebhookEvent.retry_count < self.config.max_retries,
                    or_(
                        WebhookEvent.next_retry_at.is_(None),
                        WebhookEvent.next_retry_at <= datetime.utcnow()
                    )
            ).all()
            
            for webhook in failed_webhooks:
                await self._retry_webhook(webhook)
                
                # Small delay between retries to avoid overwhelming the system
                await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error processing failed webhooks: {e}")
        finally:
            self.processing = False
    
    async def _retry_webhook(self, webhook: WebhookEvent):
        """Retry a specific webhook."""
        try:
            logger.info(f"Retrying webhook {webhook.id} (attempt {webhook.retry_count + 1})")
            
            # Update status to retrying
            webhook.processing_status = WebhookStatus.RETRYING.value
            webhook.last_retry_at = datetime.utcnow()
            webhook.retry_count += 1
            
            # Calculate next retry delay
            delay = self._calculate_retry_delay(webhook.retry_count)
            webhook.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
            
            self.db.commit()
            
            # Process the webhook
            if self.webhook_processor:
                success = await self._process_webhook(webhook)
            else:
                # Default processing logic
                success = await self._default_webhook_processing(webhook)
            
            if success:
                webhook.processing_status = WebhookStatus.SUCCESS.value
                webhook.processed_at = datetime.utcnow()
                webhook.error_message = None
                logger.info(f"Webhook {webhook.id} processed successfully on retry")
            else:
                if webhook.retry_count >= self.config.max_retries:
                    webhook.processing_status = WebhookStatus.DEAD_LETTER.value
                    webhook.error_message = "Max retries exceeded"
                    logger.warning(f"Webhook {webhook.id} moved to dead letter queue")
                else:
                    webhook.processing_status = WebhookStatus.FAILED.value
                    logger.warning(f"Webhook {webhook.id} failed on retry {webhook.retry_count}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error retrying webhook {webhook.id}: {e}")
            webhook.processing_status = WebhookStatus.FAILED.value
            webhook.error_message = str(e)
            self.db.commit()
    
    async def _process_webhook(self, webhook: WebhookEvent) -> bool:
        """Process webhook using custom processor."""
        try:
            if asyncio.iscoroutinefunction(self.webhook_processor):
                result = await self.webhook_processor(webhook)
            else:
                result = self.webhook_processor(webhook)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Custom webhook processor failed: {e}")
            return False
    
    async def _default_webhook_processing(self, webhook: WebhookEvent) -> bool:
        """Default webhook processing logic."""
        try:
            # Parse webhook payload
            payload = parse_webhook_payload(webhook.payload)
            
            # Basic validation
            if not payload or "error" in payload:
                logger.warning(f"Invalid webhook payload for {webhook.id}")
                return False
            
            # Process based on event type
            event_type = webhook.type
            
            if event_type == "payment_intent.succeeded":
                return await self._handle_payment_success(webhook, payload)
            elif event_type == "payment_intent.failed":
                return await self._handle_payment_failure(webhook, payload)
            elif event_type == "charge.succeeded":
                return await self._handle_charge_success(webhook, payload)
            elif event_type == "charge.failed":
                return await self._handle_charge_failure(webhook, payload)
            elif event_type == "subscription.created":
                return await self._handle_subscription_created(webhook, payload)
            elif event_type == "subscription.updated":
                return await self._handle_subscription_updated(webhook, payload)
            elif event_type == "subscription.deleted":
                return await self._handle_subscription_deleted(webhook, payload)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return True  # Mark as successful for unhandled types
            
        except Exception as e:
            logger.error(f"Default webhook processing failed for {webhook.id}: {e}")
            return False
    
    async def _handle_payment_success(self, webhook: WebhookEvent, payload: Dict) -> bool:
        """Handle payment success webhook."""
        try:
            # Update payment intent status
            payment_intent_id = payload.get("data", {}).get("object", {}).get("id")
            if payment_intent_id:
                # This would update your local payment intent record
                logger.info(f"Payment intent {payment_intent_id} succeeded")
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling payment success webhook: {e}")
            return False
    
    async def _handle_payment_failure(self, webhook: WebhookEvent, payload: Dict) -> bool:
        """Handle payment failure webhook."""
        try:
            payment_intent_id = payload.get("data", {}).get("object", {}).get("id")
            if payment_intent_id:
                logger.info(f"Payment intent {payment_intent_id} failed")
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling payment failure webhook: {e}")
            return False
    
    async def _handle_charge_success(self, webhook: WebhookEvent, payload: Dict) -> bool:
        """Handle charge success webhook."""
        try:
            charge_id = payload.get("data", {}).get("object", {}).get("id")
            if charge_id:
                logger.info(f"Charge {charge_id} succeeded")
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling charge success webhook: {e}")
            return False
    
    async def _handle_charge_failure(self, webhook: WebhookEvent, payload: Dict) -> bool:
        """Handle charge failure webhook."""
        try:
            charge_id = payload.get("data", {}).get("object", {}).get("id")
            if charge_id:
                logger.info(f"Charge {charge_id} failed")
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling charge failure webhook: {e}")
            return False
    
    async def _handle_subscription_created(self, webhook: WebhookEvent, payload: Dict) -> bool:
        """Handle subscription created webhook."""
        try:
            subscription_id = payload.get("data", {}).get("object", {}).get("id")
            if subscription_id:
                logger.info(f"Subscription {subscription_id} created")
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling subscription created webhook: {e}")
            return False
    
    async def _handle_subscription_updated(self, webhook: WebhookEvent, payload: Dict) -> bool:
        """Handle subscription updated webhook."""
        try:
            subscription_id = payload.get("data", {}).get("object", {}).get("id")
            if subscription_id:
                logger.info(f"Subscription {subscription_id} updated")
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling subscription updated webhook: {e}")
            return False
    
    async def _handle_subscription_deleted(self, webhook: WebhookEvent, payload: Dict) -> bool:
        """Handle subscription deleted webhook."""
        try:
            subscription_id = payload.get("data", {}).get("object", {}).get("id")
            if subscription_id:
                logger.info(f"Subscription {subscription_id} deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling subscription deleted webhook: {e}")
            return False
    
    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        # Exponential backoff
        delay = min(
            self.config.initial_delay * (self.config.backoff_multiplier ** (retry_count - 1)),
            self.config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.config.jitter_factor * (2 * time.random() - 1)
        delay += jitter
        
        return max(delay, 0.1)  # Minimum 100ms delay
    
    def get_dead_letter_queue(self) -> List[WebhookEvent]:
        """Get webhooks in the dead letter queue."""
        return self.db.query(WebhookEvent).filter(
            WebhookEvent.processing_status == WebhookStatus.DEAD_LETTER.value
        ).all()
    
    def retry_dead_letter_webhook(self, webhook_id: str) -> bool:
        """Manually retry a webhook from the dead letter queue."""
        webhook = self.db.query(WebhookEvent).filter(WebhookEvent.id == webhook_id).first()
        
        if not webhook:
            logger.error(f"Webhook {webhook_id} not found")
            return False
        
        if webhook.processing_status != WebhookStatus.DEAD_LETTER.value:
            logger.warning(f"Webhook {webhook_id} is not in dead letter queue")
            return False
        
        try:
            # Reset retry count and move back to pending
            webhook.retry_count = 0
            webhook.processing_status = WebhookStatus.PENDING.value
            webhook.next_retry_at = datetime.utcnow()
            webhook.error_message = None
            
            self.db.commit()
            logger.info(f"Webhook {webhook_id} moved from dead letter queue to pending")
            return True
            
        except Exception as e:
            logger.error(f"Error retrying dead letter webhook {webhook_id}: {e}")
            self.db.rollback()
            return False
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get statistics about webhook retries."""
        total_webhooks = self.db.query(WebhookEvent).count()
        pending_webhooks = self.db.query(WebhookEvent).filter(
            WebhookEvent.processing_status == WebhookStatus.PENDING.value
        ).count()
        failed_webhooks = self.db.query(WebhookEvent).filter(
            WebhookEvent.processing_status == WebhookStatus.FAILED.value
        ).count()
        retrying_webhooks = self.db.query(WebhookEvent).filter(
            WebhookEvent.processing_status == WebhookStatus.RETRYING.value
        ).count()
        successful_webhooks = self.db.query(WebhookEvent).filter(
            WebhookEvent.processing_status == WebhookStatus.SUCCESS.value
        ).count()
        dead_letter_webhooks = self.db.query(WebhookEvent).filter(
            WebhookEvent.processing_status == WebhookStatus.DEAD_LETTER.value
        ).count()
        
        return {
            "total": total_webhooks,
            "pending": pending_webhooks,
            "failed": failed_webhooks,
            "retrying": retrying_webhooks,
            "successful": successful_webhooks,
            "dead_letter": dead_letter_webhooks,
            "success_rate": (successful_webhooks / total_webhooks * 100) if total_webhooks > 0 else 0
        }
    
    def cleanup_old_webhooks(self, days_to_keep: int = 90):
        """Clean up old webhook events to prevent database bloat."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old successful webhooks
            deleted_count = self.db.query(WebhookEvent).filter(
                and_(
                    WebhookEvent.processing_status == WebhookStatus.SUCCESS.value,
                    WebhookEvent.created_at < cutoff_date
                )
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old webhook events")
            
        except Exception as e:
            logger.error(f"Error cleaning up old webhooks: {e}")
            self.db.rollback()


class WebhookRetryWorker:
    """Background worker for processing webhook retries."""
    
    def __init__(
        self,
        retry_service: WebhookRetryService,
        poll_interval: float = 60.0,
        max_concurrent: int = 5
    ):
        self.retry_service = retry_service
        self.poll_interval = poll_interval
        self.max_concurrent = max_concurrent
        self.running = False
        self.tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start the webhook retry worker."""
        if self.running:
            logger.warning("Webhook retry worker already running")
            return
        
        self.running = True
        logger.info("Starting webhook retry worker")
        
        try:
            while self.running:
                # Process failed webhooks
                await self.retry_service.process_failed_webhooks()
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval)
        
        except asyncio.CancelledError:
            logger.info("Webhook retry worker cancelled")
        except Exception as e:
            logger.error(f"Webhook retry worker error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Stop the webhook retry worker."""
        self.running = False
        logger.info("Stopping webhook retry worker")
        
        # Cancel any running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
    
    async def process_webhook_batch(self, webhooks: List[WebhookEvent]):
        """Process a batch of webhooks concurrently."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_with_semaphore(webhook):
            async with semaphore:
                await self.retry_service._retry_webhook(webhook)
        
        tasks = [process_with_semaphore(webhook) for webhook in webhooks]
        await asyncio.gather(*tasks, return_exceptions=True)
