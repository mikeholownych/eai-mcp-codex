"""Payment webhook handler for processing gateway notifications."""

import logging
import hashlib
import hmac
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from fastapi import HTTPException, Request, Depends
from pydantic import BaseModel

from .gateways.factory import PaymentGatewayFactory
from .models import PaymentIntent, Charge, Refund, Customer
from .database import get_db_session
from .utils import create_audit_log
from .config import get_settings

logger = logging.getLogger(__name__)

# Webhook event types
WEBHOOK_EVENTS = {
    "stripe": {
        "payment_intent.succeeded": "payment_intent_succeeded",
        "payment_intent.payment_failed": "payment_intent_failed",
        "payment_intent.canceled": "payment_intent_canceled",
        "charge.succeeded": "charge_succeeded",
        "charge.failed": "charge_failed",
        "charge.refunded": "charge_refunded",
        "customer.created": "customer_created",
        "customer.updated": "customer_updated",
        "customer.deleted": "customer_deleted",
        "invoice.payment_succeeded": "invoice_payment_succeeded",
        "invoice.payment_failed": "invoice_payment_failed",
        "subscription.created": "subscription_created",
        "subscription.updated": "subscription_updated",
        "subscription.deleted": "subscription_deleted",
    },
    "paypal": {
        "PAYMENT.CAPTURE.COMPLETED": "payment_capture_completed",
        "PAYMENT.CAPTURE.DENIED": "payment_capture_denied",
        "PAYMENT.CAPTURE.REFUNDED": "payment_capture_refunded",
        "PAYMENT.CAPTURE.REVERSED": "payment_capture_reversed",
        "PAYMENT.CAPTURE.PENDING": "payment_capture_pending",
        "BILLING.SUBSCRIPTION.CREATED": "subscription_created",
        "BILLING.SUBSCRIPTION.UPDATED": "subscription_updated",
        "BILLING.SUBSCRIPTION.CANCELLED": "subscription_cancelled",
        "BILLING.SUBSCRIPTION.EXPIRED": "subscription_expired",
    }
}

# Webhook event handlers
WEBHOOK_HANDLERS = {
    "payment_intent_succeeded": "handle_payment_intent_succeeded",
    "payment_intent_failed": "handle_payment_intent_failed",
    "payment_intent_canceled": "handle_payment_intent_canceled",
    "charge_succeeded": "handle_charge_succeeded",
    "charge_failed": "handle_charge_failed",
    "charge_refunded": "handle_charge_refunded",
    "customer_created": "handle_customer_created",
    "customer_updated": "handle_customer_updated",
    "customer_deleted": "handle_customer_deleted",
    "invoice_payment_succeeded": "handle_invoice_payment_succeeded",
    "invoice_payment_failed": "handle_invoice_payment_failed",
    "subscription_created": "handle_subscription_created",
    "subscription_updated": "handle_subscription_updated",
    "subscription_deleted": "handle_subscription_deleted",
    "payment_capture_completed": "handle_payment_capture_completed",
    "payment_capture_denied": "handle_payment_capture_denied",
    "payment_capture_refunded": "handle_payment_capture_refunded",
    "payment_capture_reversed": "handle_payment_capture_reversed",
    "payment_capture_pending": "handle_payment_capture_pending",
    "subscription_cancelled": "handle_subscription_cancelled",
    "subscription_expired": "handle_subscription_expired",
}


class WebhookHandler:
    """Handles payment webhook events from various gateways."""
    
    def __init__(self):
        self.gateway_factory = PaymentGatewayFactory()
        self.settings = get_settings()
    
    async def verify_webhook_signature(
        self,
        request: Request,
        gateway_name: str
    ) -> bool:
        """Verify webhook signature for security."""
        try:
            if gateway_name == "stripe":
                return await self._verify_stripe_signature(request)
            elif gateway_name == "paypal":
                return await self._verify_paypal_signature(request)
            else:
                logger.warning("Unknown gateway for signature verification: %s", gateway_name)
                return True  # Allow unknown gateways for now
        except Exception as e:
            logger.error("Failed to verify webhook signature: %s", str(e))
            return False
    
    async def _verify_stripe_signature(self, request: Request) -> bool:
        """Verify Stripe webhook signature."""
        try:
            # Get webhook secret from settings
            webhook_secret = self.settings.stripe_webhook_secret
            if not webhook_secret:
                logger.warning("No Stripe webhook secret configured")
                return True
            
            # Get signature from headers
            signature = request.headers.get("stripe-signature")
            if not signature:
                logger.error("No Stripe signature found in headers")
                return False
            
            # Get raw body
            body = await request.body()
            
            # Verify signature
            try:
                import stripe
                stripe.Webhook.construct_event(
                    body,
                    signature,
                    webhook_secret
                )
                return True
            except Exception as e:
                logger.error("Stripe signature verification failed: %s", str(e))
                return False
                
        except Exception as e:
            logger.error("Stripe signature verification error: %s", str(e))
            return False
    
    async def _verify_paypal_signature(self, request: Request) -> bool:
        """Verify PayPal webhook signature."""
        try:
            # Get webhook secret from settings
            webhook_secret = self.settings.paypal_webhook_secret
            if not webhook_secret:
                logger.warning("No PayPal webhook secret configured")
                return True
            
            # Get signature from headers
            signature = request.headers.get("paypal-signature")
            if not signature:
                logger.error("No PayPal signature found in headers")
                return False
            
            # Get raw body
            body = await request.body()
            
            # Verify signature using HMAC
            expected_signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
                
        except Exception as e:
            logger.error("PayPal signature verification error: %s", str(e))
            return False
    
    async def process_webhook(
        self,
        request: Request,
        gateway_name: str
    ) -> Dict[str, Any]:
        """Process webhook event from payment gateway."""
        try:
            # Verify webhook signature
            if not await self.verify_webhook_signature(request, gateway_name):
                raise HTTPException(status_code=400, detail="Invalid webhook signature")
            
            # Parse webhook body
            body = await request.json()
            logger.info("Received webhook from %s: %s", gateway_name, body.get("type", "unknown"))
            
            # Extract event type
            event_type = self._extract_event_type(gateway_name, body)
            if not event_type:
                logger.warning("Unknown webhook event type from %s: %s", gateway_name, body)
                return {"status": "ignored", "reason": "unknown_event_type"}
            
            # Map to internal event type
            internal_event_type = WEBHOOK_EVENTS.get(gateway_name, {}).get(event_type)
            if not internal_event_type:
                logger.warning("Unmapped webhook event type: %s", event_type)
                return {"status": "ignored", "reason": "unmapped_event_type"}
            
            # Get handler method
            handler_method = WEBHOOK_HANDLERS.get(internal_event_type)
            if not handler_method:
                logger.warning("No handler for event type: %s", internal_event_type)
                return {"status": "ignored", "reason": "no_handler"}
            
            # Call handler
            handler = getattr(self, handler_method, None)
            if handler and callable(handler):
                result = await handler(body, gateway_name)
                return {"status": "processed", "event_type": internal_event_type, "result": result}
            else:
                logger.warning("Handler method not found: %s", handler_method)
                return {"status": "ignored", "reason": "handler_not_found"}
                
        except Exception as e:
            logger.error("Failed to process webhook from %s: %s", gateway_name, str(e))
            raise HTTPException(status_code=500, detail="Webhook processing failed")
    
    def _extract_event_type(self, gateway_name: str, body: Dict[str, Any]) -> Optional[str]:
        """Extract event type from webhook body."""
        if gateway_name == "stripe":
            return body.get("type")
        elif gateway_name == "paypal":
            return body.get("event_type")
        else:
            return body.get("type") or body.get("event_type")
    
    # Webhook event handlers
    async def handle_payment_intent_succeeded(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle payment intent succeeded event."""
        try:
            db_session = get_db_session()
            
            # Extract payment intent data
            if gateway_name == "stripe":
                payment_intent_data = body.get("data", {}).get("object", {})
                payment_intent_id = payment_intent_data.get("id")
                customer_id = payment_intent_data.get("customer")
                amount = payment_intent_data.get("amount")
                currency = payment_intent_data.get("currency")
            elif gateway_name == "paypal":
                payment_intent_data = body.get("resource", {})
                payment_intent_id = payment_intent_data.get("id")
                customer_id = payment_intent_data.get("payer", {}).get("payer_id")
                amount = payment_intent_data.get("amount", {}).get("value")
                currency = payment_intent_data.get("amount", {}).get("currency_code")
            else:
                logger.warning("Unknown gateway for payment intent succeeded: %s", gateway_name)
                return {"status": "ignored"}
            
            # Update payment intent in database
            payment_intent = db_session.query(PaymentIntent).filter(
                PaymentIntent.provider_id == payment_intent_id
            ).first()
            
            if payment_intent:
                payment_intent.status = "succeeded"
                payment_intent.updated_at = datetime.utcnow()
                db_session.commit()
                
                # Create audit log
                await create_audit_log(
                    db_session,
                    actor="webhook",
                    action="payment_intent_succeeded",
                    resource_type="payment_intent",
                    resource_id=payment_intent.id,
                    metadata={
                        "gateway": gateway_name,
                        "external_id": payment_intent_id,
                        "amount": amount,
                        "currency": currency
                    }
                )
                
                logger.info("Updated payment intent %s status to succeeded", payment_intent.id)
                return {"status": "updated", "payment_intent_id": str(payment_intent.id)}
            else:
                logger.warning("Payment intent not found in database: %s", payment_intent_id)
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error("Failed to handle payment intent succeeded: %s", str(e))
            return {"status": "error", "error": str(e)}
    
    async def handle_payment_intent_failed(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle payment intent failed event."""
        try:
            db_session = get_db_session()
            
            # Extract payment intent data
            if gateway_name == "stripe":
                payment_intent_data = body.get("data", {}).get("object", {})
                payment_intent_id = payment_intent_data.get("id")
                failure_reason = payment_intent_data.get("last_payment_error", {}).get("message")
            elif gateway_name == "paypal":
                payment_intent_data = body.get("resource", {})
                payment_intent_id = payment_intent_data.get("id")
                failure_reason = body.get("summary", "Payment failed")
            else:
                logger.warning("Unknown gateway for payment intent failed: %s", gateway_name)
                return {"status": "ignored"}
            
            # Update payment intent in database
            payment_intent = db_session.query(PaymentIntent).filter(
                PaymentIntent.provider_id == payment_intent_id
            ).first()
            
            if payment_intent:
                payment_intent.status = "failed"
                payment_intent.updated_at = datetime.utcnow()
                db_session.commit()
                
                # Create audit log
                await create_audit_log(
                    db_session,
                    actor="webhook",
                    action="payment_intent_failed",
                    resource_type="payment_intent",
                    resource_id=payment_intent.id,
                    metadata={
                        "gateway": gateway_name,
                        "external_id": payment_intent_id,
                        "failure_reason": failure_reason
                    }
                )
                
                logger.info("Updated payment intent %s status to failed", payment_intent.id)
                return {"status": "updated", "payment_intent_id": str(payment_intent.id)}
            else:
                logger.warning("Payment intent not found in database: %s", payment_intent_id)
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error("Failed to handle payment intent failed: %s", str(e))
            return {"status": "error", "error": str(e)}
    
    async def handle_charge_succeeded(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle charge succeeded event."""
        try:
            db_session = get_db_session()
            
            # Extract charge data
            if gateway_name == "stripe":
                charge_data = body.get("data", {}).get("object", {})
                charge_id = charge_data.get("id")
                payment_intent_id = charge_data.get("payment_intent")
                amount = charge_data.get("amount")
                currency = charge_data.get("currency")
                receipt_url = charge_data.get("receipt_url")
            elif gateway_name == "paypal":
                charge_data = body.get("resource", {})
                charge_id = charge_data.get("id")
                payment_intent_id = charge_data.get("custom_id")  # Assuming custom_id stores payment intent
                amount = charge_data.get("amount", {}).get("value")
                currency = charge_data.get("amount", {}).get("currency_code")
                receipt_url = charge_data.get("links", [{}])[0].get("href") if charge_data.get("links") else None
            else:
                logger.warning("Unknown gateway for charge succeeded: %s", gateway_name)
                return {"status": "ignored"}
            
            # Create or update charge in database
            charge = db_session.query(Charge).filter(
                Charge.provider_charge_id == charge_id
            ).first()
            
            if not charge:
                # Find payment intent
                payment_intent = db_session.query(PaymentIntent).filter(
                    PaymentIntent.provider_id == payment_intent_id
                ).first()
                
                if payment_intent:
                    charge = Charge(
                        payment_intent_id=payment_intent.id,
                        provider_charge_id=charge_id,
                        status="succeeded",
                        receipt_url=receipt_url
                    )
                    db_session.add(charge)
                    db_session.commit()
                    
                    # Create audit log
                    await create_audit_log(
                        db_session,
                        actor="webhook",
                        action="charge_created",
                        resource_type="charge",
                        resource_id=charge.id,
                        metadata={
                            "gateway": gateway_name,
                            "external_id": charge_id,
                            "amount": amount,
                            "currency": currency
                        }
                    )
                    
                    logger.info("Created charge %s from webhook", charge.id)
                    return {"status": "created", "charge_id": str(charge.id)}
                else:
                    logger.warning("Payment intent not found for charge: %s", payment_intent_id)
                    return {"status": "not_found"}
            else:
                # Update existing charge
                charge.status = "succeeded"
                charge.receipt_url = receipt_url
                db_session.commit()
                
                logger.info("Updated charge %s status to succeeded", charge.id)
                return {"status": "updated", "charge_id": str(charge.id)}
                
        except Exception as e:
            logger.error("Failed to handle charge succeeded: %s", str(e))
            return {"status": "error", "error": str(e)}
    
    async def handle_charge_refunded(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle charge refunded event."""
        try:
            db_session = get_db_session()
            
            # Extract refund data
            if gateway_name == "stripe":
                refund_data = body.get("data", {}).get("object", {})
                refund_id = refund_data.get("id")
                charge_id = refund_data.get("charge")
                amount = refund_data.get("amount")
                currency = refund_data.get("currency")
                reason = refund_data.get("reason")
            elif gateway_name == "paypal":
                refund_data = body.get("resource", {})
                refund_id = refund_data.get("id")
                charge_id = refund_data.get("capture_id")
                amount = refund_data.get("amount", {}).get("value")
                currency = refund_data.get("amount", {}).get("currency_code")
                reason = refund_data.get("note_to_payer")
            else:
                logger.warning("Unknown gateway for charge refunded: %s", gateway_name)
                return {"status": "ignored"}
            
            # Find charge in database
            charge = db_session.query(Charge).filter(
                Charge.provider_charge_id == charge_id
            ).first()
            
            if charge:
                # Create refund record
                refund = Refund(
                    charge_id=charge.id,
                    provider_refund_id=refund_id,
                    amount_minor=int(float(amount) * 100) if amount else None,
                    status="succeeded",
                    reason=reason
                )
                db_session.add(refund)
                db_session.commit()
                
                # Create audit log
                await create_audit_log(
                    db_session,
                    actor="webhook",
                    action="refund_created",
                    resource_type="charge",
                    resource_id=charge.id,
                    metadata={
                        "gateway": gateway_name,
                        "refund_id": refund_id,
                        "amount": amount,
                        "currency": currency,
                        "reason": reason
                    }
                )
                
                logger.info("Created refund %s from webhook", refund.id)
                return {"status": "created", "refund_id": str(refund.id)}
            else:
                logger.warning("Charge not found for refund: %s", charge_id)
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error("Failed to handle charge refunded: %s", str(e))
            return {"status": "error", "error": str(e)}
    
    # Additional handlers for other event types
    async def handle_customer_created(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle customer created event."""
        logger.info("Customer created event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_customer_updated(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle customer updated event."""
        logger.info("Customer updated event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_customer_deleted(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle customer deleted event."""
        logger.info("Customer deleted event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_invoice_payment_succeeded(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle invoice payment succeeded event."""
        logger.info("Invoice payment succeeded event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_invoice_payment_failed(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle invoice payment failed event."""
        logger.info("Invoice payment failed event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_subscription_created(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle subscription created event."""
        logger.info("Subscription created event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_subscription_updated(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle subscription updated event."""
        logger.info("Subscription updated event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_subscription_deleted(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle subscription deleted event."""
        logger.info("Subscription deleted event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_payment_capture_completed(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle PayPal payment capture completed event."""
        return await self.handle_charge_succeeded(body, gateway_name)
    
    async def handle_payment_capture_denied(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle PayPal payment capture denied event."""
        logger.info("Payment capture denied event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_payment_capture_refunded(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle PayPal payment capture refunded event."""
        return await self.handle_charge_refunded(body, gateway_name)
    
    async def handle_payment_capture_reversed(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle PayPal payment capture reversed event."""
        logger.info("Payment capture reversed event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_payment_capture_pending(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle PayPal payment capture pending event."""
        logger.info("Payment capture pending event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_subscription_cancelled(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle PayPal subscription cancelled event."""
        return await self.handle_subscription_deleted(body, gateway_name)
    
    async def handle_subscription_expired(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle PayPal subscription expired event."""
        logger.info("Subscription expired event from %s", gateway_name)
        return {"status": "processed"}
    
    async def handle_payment_intent_canceled(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle payment intent canceled event."""
        try:
            db_session = get_db_session()
            
            # Extract payment intent data
            if gateway_name == "stripe":
                payment_intent_data = body.get("data", {}).get("object", {})
                payment_intent_id = payment_intent_data.get("id")
            elif gateway_name == "paypal":
                payment_intent_data = body.get("resource", {})
                payment_intent_id = payment_intent_data.get("id")
            else:
                logger.warning("Unknown gateway for payment intent canceled: %s", gateway_name)
                return {"status": "ignored"}
            
            # Update payment intent in database
            payment_intent = db_session.query(PaymentIntent).filter(
                PaymentIntent.provider_id == payment_intent_id
            ).first()
            
            if payment_intent:
                payment_intent.status = "canceled"
                payment_intent.updated_at = datetime.utcnow()
                db_session.commit()
                
                # Create audit log
                await create_audit_log(
                    db_session,
                    actor="webhook",
                    action="payment_intent_canceled",
                    resource_type="payment_intent",
                    resource_id=payment_intent.id,
                    metadata={
                        "gateway": gateway_name,
                        "external_id": payment_intent_id
                    }
                )
                
                logger.info("Updated payment intent %s status to canceled", payment_intent.id)
                return {"status": "updated", "payment_intent_id": str(payment_intent.id)}
            else:
                logger.warning("Payment intent not found in database: %s", payment_intent_id)
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error("Failed to handle payment intent canceled: %s", str(e))
            return {"status": "error", "error": str(e)}
    
    async def handle_charge_failed(self, body: Dict[str, Any], gateway_name: str) -> Dict[str, Any]:
        """Handle charge failed event."""
        try:
            db_session = get_db_session()
            
            # Extract charge data
            if gateway_name == "stripe":
                charge_data = body.get("data", {}).get("object", {})
                charge_id = charge_data.get("id")
                failure_reason = charge_data.get("failure_message")
            elif gateway_name == "paypal":
                charge_data = body.get("resource", {})
                charge_id = charge_data.get("id")
                failure_reason = body.get("summary", "Charge failed")
            else:
                logger.warning("Unknown gateway for charge failed: %s", gateway_name)
                return {"status": "ignored"}
            
            # Update charge in database
            charge = db_session.query(Charge).filter(
                Charge.provider_charge_id == charge_id
            ).first()
            
            if charge:
                charge.status = "failed"
                db_session.commit()
                
                # Create audit log
                await create_audit_log(
                    db_session,
                    actor="webhook",
                    action="charge_failed",
                    resource_type="charge",
                    resource_id=charge.id,
                    metadata={
                        "gateway": gateway_name,
                        "external_id": charge_id,
                        "failure_reason": failure_reason
                    }
                )
                
                logger.info("Updated charge %s status to failed", charge.id)
                return {"status": "updated", "charge_id": str(charge.id)}
            else:
                logger.warning("Charge not found in database: %s", charge_id)
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error("Failed to handle charge failed: %s", str(e))
            return {"status": "error", "error": str(e)}


# Webhook endpoint handlers
async def handle_stripe_webhook(
    request: Request,
    webhook_handler: WebhookHandler = Depends(lambda: WebhookHandler())
) -> Dict[str, Any]:
    """Handle Stripe webhook events."""
    return await webhook_handler.process_webhook(request, "stripe")


async def handle_paypal_webhook(
    request: Request,
    webhook_handler: WebhookHandler = Depends(lambda: WebhookHandler())
) -> Dict[str, Any]:
    """Handle PayPal webhook events."""
    return await webhook_handler.process_webhook(request, "paypal")
