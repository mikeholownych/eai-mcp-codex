"""Payment webhook handlers for processing gateway notifications."""

import logging
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer

from .service import PaymentService
from .gateways.factory import PaymentGatewayFactory
from .models import PaymentIntent, Charge, Refund
from .database import get_db_session
from .utils import create_audit_log

logger = logging.getLogger(__name__)
security = HTTPBearer()


class WebhookHandler:
    """Base webhook handler for payment gateways."""
    
    def __init__(self, payment_service: PaymentService):
        self.payment_service = payment_service
    
    async def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Process webhook payload from payment gateway."""
        raise NotImplementedError("Subclasses must implement process_webhook")


class StripeWebhookHandler(WebhookHandler):
    """Stripe webhook handler."""
    
    def __init__(self, payment_service: PaymentService, webhook_secret: str):
        super().__init__(payment_service)
        self.webhook_secret = webhook_secret
    
    def _verify_signature(self, payload: bytes, signature: str, timestamp: str) -> bool:
        """Verify Stripe webhook signature."""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                f"{timestamp}.{payload.decode('utf-8')}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"t={timestamp},v1={expected_signature}", signature)
        except Exception as e:
            logger.error("Failed to verify Stripe webhook signature: %s", str(e))
            return False
    
    async def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Process Stripe webhook."""
        try:
            # Verify webhook signature
            signature = headers.get("stripe-signature", "")
            if not signature:
                raise HTTPException(status_code=400, detail="Missing Stripe signature")
            
            # Extract timestamp and signature from header
            parts = signature.split(",")
            timestamp = None
            sig = None
            
            for part in parts:
                if part.startswith("t="):
                    timestamp = part[2:]
                elif part.startswith("v1="):
                    sig = part[3:]
            
            if not timestamp or not sig:
                raise HTTPException(status_code=400, detail="Invalid Stripe signature format")
            
            # Verify signature
            payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            if not self._verify_signature(payload_bytes, sig, timestamp):
                raise HTTPException(status_code=400, detail="Invalid Stripe signature")
            
            # Process webhook event
            event_type = payload.get("type")
            event_data = payload.get("data", {}).get("object", {})
            
            logger.info("Processing Stripe webhook: %s", event_type)
            
            if event_type == "payment_intent.succeeded":
                return await self._handle_payment_intent_succeeded(event_data)
            elif event_type == "payment_intent.payment_failed":
                return await self._handle_payment_intent_failed(event_data)
            elif event_type == "charge.succeeded":
                return await self._handle_charge_succeeded(event_data)
            elif event_type == "charge.failed":
                return await self._handle_charge_failed(event_data)
            elif event_type == "charge.refunded":
                return await self._handle_charge_refunded(event_data)
            elif event_type == "invoice.payment_succeeded":
                return await self._handle_invoice_payment_succeeded(event_data)
            elif event_type == "invoice.payment_failed":
                return await self._handle_invoice_payment_failed(event_data)
            else:
                logger.info("Unhandled Stripe webhook event: %s", event_type)
                return {"status": "ignored", "event_type": event_type}
                
        except Exception as e:
            logger.error("Failed to process Stripe webhook: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
    
    async def _handle_payment_intent_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment intent."""
        payment_intent_id = event_data.get("id")
        amount = event_data.get("amount")
        currency = event_data.get("currency")
        
        # Update payment intent status in database
        await self.payment_service.update_payment_intent_status(
            payment_intent_id, "succeeded"
        )
        
        # Create audit log
        await create_audit_log(
            "payment_intent_succeeded",
            payment_intent_id,
            {"amount": amount, "currency": currency}
        )
        
        return {"status": "processed", "event": "payment_intent_succeeded"}
    
    async def _handle_payment_intent_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment intent."""
        payment_intent_id = event_data.get("id")
        last_payment_error = event_data.get("last_payment_error", {})
        
        # Update payment intent status in database
        await self.payment_service.update_payment_intent_status(
            payment_intent_id, "failed"
        )
        
        # Create audit log
        await create_audit_log(
            "payment_intent_failed",
            payment_intent_id,
            {"error": last_payment_error}
        )
        
        return {"status": "processed", "event": "payment_intent_failed"}
    
    async def _handle_charge_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful charge."""
        charge_id = event_data.get("id")
        amount = event_data.get("amount")
        currency = event_data.get("currency")
        
        # Update charge status in database
        await self.payment_service.update_charge_status(
            charge_id, "succeeded"
        )
        
        # Create audit log
        await create_audit_log(
            "charge_succeeded",
            charge_id,
            {"amount": amount, "currency": currency}
        )
        
        return {"status": "processed", "event": "charge_succeeded"}
    
    async def _handle_charge_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed charge."""
        charge_id = event_data.get("id")
        failure_message = event_data.get("failure_message", "")
        
        # Update charge status in database
        await self.payment_service.update_charge_status(
            charge_id, "failed"
        )
        
        # Create audit log
        await create_audit_log(
            "charge_failed",
            charge_id,
            {"failure_message": failure_message}
        )
        
        return {"status": "processed", "event": "charge_failed"}
    
    async def _handle_charge_refunded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge refund."""
        charge_id = event_data.get("id")
        amount_refunded = event_data.get("amount_refunded")
        
        # Update charge status in database
        await self.payment_service.update_charge_status(
            charge_id, "refunded"
        )
        
        # Create audit log
        await create_audit_log(
            "charge_refunded",
            charge_id,
            {"amount_refunded": amount_refunded}
        )
        
        return {"status": "processed", "event": "charge_refunded"}
    
    async def _handle_invoice_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful invoice payment."""
        invoice_id = event_data.get("id")
        amount_paid = event_data.get("amount_paid")
        currency = event_data.get("currency")
        
        # Create audit log
        await create_audit_log(
            "invoice_payment_succeeded",
            invoice_id,
            {"amount_paid": amount_paid, "currency": currency}
        )
        
        return {"status": "processed", "event": "invoice_payment_succeeded"}
    
    async def _handle_invoice_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed invoice payment."""
        invoice_id = event_data.get("id")
        attempt_count = event_data.get("attempt_count", 0)
        
        # Create audit log
        await create_audit_log(
            "invoice_payment_failed",
            invoice_id,
            {"attempt_count": attempt_count}
        )
        
        return {"status": "processed", "event": "invoice_payment_failed"}


class PayPalWebhookHandler(WebhookHandler):
    """PayPal webhook handler."""
    
    def __init__(self, payment_service: PaymentService):
        super().__init__(payment_service)
    
    async def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Process PayPal webhook."""
        try:
            event_type = payload.get("event_type")
            resource = payload.get("resource", {})
            
            logger.info("Processing PayPal webhook: %s", event_type)
            
            if event_type == "PAYMENT.CAPTURE.COMPLETED":
                return await self._handle_payment_capture_completed(resource)
            elif event_type == "PAYMENT.CAPTURE.DENIED":
                return await self._handle_payment_capture_denied(resource)
            elif event_type == "PAYMENT.CAPTURE.REFUNDED":
                return await self._handle_payment_capture_refunded(resource)
            elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
                return await self._handle_subscription_activated(resource)
            elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
                return await self._handle_subscription_cancelled(resource)
            else:
                logger.info("Unhandled PayPal webhook event: %s", event_type)
                return {"status": "ignored", "event_type": event_type}
                
        except Exception as e:
            logger.error("Failed to process PayPal webhook: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
    
    async def _handle_payment_capture_completed(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Handle completed payment capture."""
        capture_id = resource.get("id")
        amount = resource.get("amount", {})
        
        # Update charge status in database
        await self.payment_service.update_charge_status(
            capture_id, "succeeded"
        )
        
        # Create audit log
        await create_audit_log(
            "paypal_payment_completed",
            capture_id,
            {"amount": amount}
        )
        
        return {"status": "processed", "event": "payment_capture_completed"}
    
    async def _handle_payment_capture_denied(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Handle denied payment capture."""
        capture_id = resource.get("id")
        
        # Update charge status in database
        await self.payment_service.update_charge_status(
            capture_id, "failed"
        )
        
        # Create audit log
        await create_audit_log(
            "paypal_payment_denied",
            capture_id,
            {}
        )
        
        return {"status": "processed", "event": "payment_capture_denied"}
    
    async def _handle_payment_capture_refunded(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refunded payment capture."""
        capture_id = resource.get("id")
        
        # Update charge status in database
        await self.payment_service.update_charge_status(
            capture_id, "refunded"
        )
        
        # Create audit log
        await create_audit_log(
            "paypal_payment_refunded",
            capture_id,
            {}
        )
        
        return {"status": "processed", "event": "payment_capture_refunded"}
    
    async def _handle_subscription_activated(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription activation."""
        subscription_id = resource.get("id")
        
        # Create audit log
        await create_audit_log(
            "paypal_subscription_activated",
            subscription_id,
            {}
        )
        
        return {"status": "processed", "event": "subscription_activated"}
    
    async def _handle_subscription_cancelled(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation."""
        subscription_id = resource.get("id")
        
        # Create audit log
        await create_audit_log(
            "paypal_subscription_cancelled",
            subscription_id,
            {}
        )
        
        return {"status": "processed", "event": "subscription_cancelled"}


class AdyenWebhookHandler(WebhookHandler):
    """Adyen webhook handler."""
    
    def __init__(self, payment_service: PaymentService):
        super().__init__(payment_service)
    
    async def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Process Adyen webhook."""
        try:
            notification_items = payload.get("notificationItems", [])
            
            logger.info("Processing Adyen webhook with %d notification items", len(notification_items))
            
            results = []
            for item in notification_items:
                notification_request_item = item.get("NotificationRequestItem", {})
                event_type = notification_request_item.get("eventCode")
                
                if event_type == "AUTHORISATION":
                    result = await self._handle_authorisation(notification_request_item)
                elif event_type == "CAPTURE":
                    result = await self._handle_capture(notification_request_item)
                elif event_type == "REFUND":
                    result = await self._handle_refund(notification_request_item)
                elif event_type == "CANCELLATION":
                    result = await self._handle_cancellation(notification_request_item)
                else:
                    result = {"status": "ignored", "event_type": event_type}
                
                results.append(result)
            
            return {"status": "processed", "results": results}
                
        except Exception as e:
            logger.error("Failed to process Adyen webhook: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
    
    async def _handle_authorisation(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authorisation event."""
        psp_reference = notification.get("pspReference")
        success = notification.get("success", "false").lower() == "true"
        
        if success:
            # Update payment intent status
            await self.payment_service.update_payment_intent_status(
                psp_reference, "succeeded"
            )
            
            # Create audit log
            await create_audit_log(
                "adyen_authorisation_succeeded",
                psp_reference,
                {}
            )
        else:
            # Update payment intent status
            await self.payment_service.update_payment_intent_status(
                psp_reference, "failed"
            )
            
            # Create audit log
            await create_audit_log(
                "adyen_authorisation_failed",
                psp_reference,
                {}
            )
        
        return {"status": "processed", "event": "authorisation", "success": success}
    
    async def _handle_capture(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle capture event."""
        psp_reference = notification.get("pspReference")
        
        # Update charge status
        await self.payment_service.update_charge_status(
            psp_reference, "succeeded"
        )
        
        # Create audit log
        await create_audit_log(
            "adyen_capture_succeeded",
            psp_reference,
            {}
        )
        
        return {"status": "processed", "event": "capture"}
    
    async def _handle_refund(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refund event."""
        psp_reference = notification.get("pspReference")
        
        # Update charge status
        await self.payment_service.update_charge_status(
            psp_reference, "refunded"
        )
        
        # Create audit log
        await create_audit_log(
            "adyen_refund_processed",
            psp_reference,
            {}
        )
        
        return {"status": "processed", "event": "refund"}
    
    async def _handle_cancellation(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cancellation event."""
        psp_reference = notification.get("pspReference")
        
        # Update payment intent status
        await self.payment_service.update_payment_intent_status(
            psp_reference, "cancelled"
        )
        
        # Create audit log
        await create_audit_log(
            "adyen_payment_cancelled",
            psp_reference,
            {}
        )
        
        return {"status": "processed", "event": "cancellation"}


class WebhookManager:
    """Manager for handling webhooks from different payment gateways."""
    
    def __init__(self, payment_service: PaymentService):
        self.payment_service = payment_service
        self.handlers = {
            "stripe": StripeWebhookHandler(payment_service, ""),  # Secret will be set from config
            "paypal": PayPalWebhookHandler(payment_service),
            "adyen": AdyenWebhookHandler(payment_service)
        }
    
    async def process_webhook(
        self, 
        gateway: str, 
        payload: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process webhook from specified gateway."""
        if gateway not in self.handlers:
            raise HTTPException(status_code=400, detail=f"Unsupported gateway: {gateway}")
        
        handler = self.handlers[gateway]
        return await handler.process_webhook(payload, headers)


async def get_webhook_manager(
    payment_service: PaymentService = Depends(lambda: PaymentService())
) -> WebhookManager:
    """Get webhook manager instance."""
    return WebhookManager(payment_service)
