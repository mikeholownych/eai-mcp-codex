"""Payment API router for FastAPI."""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from .service import PaymentService
from .webhooks import get_webhook_manager, WebhookManager
from .models import Customer, PaymentIntent as DBPaymentIntent, Charge as DBCharge
from .gateways.base import PaymentIntent, Charge, Refund, PaymentMethod

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/payments", tags=["payments"])


# Request/Response Models
class CreateCustomerRequest(BaseModel):
    email: str
    country: str
    metadata: Optional[Dict[str, Any]] = None


class CreateCustomerResponse(BaseModel):
    customer_id: str
    email: str
    country: str
    created_at: str


class CreatePaymentIntentRequest(BaseModel):
    amount_minor: int
    currency: str
    customer_id: str
    capture_method: str = "automatic"
    confirmation_method: str = "automatic"
    metadata: Optional[Dict[str, Any]] = None
    payment_method_types: Optional[List[str]] = None


class CreatePaymentIntentResponse(BaseModel):
    payment_intent_id: str
    amount_minor: int
    currency: str
    status: str
    client_secret: str
    capture_method: str
    confirmation_method: str


class ConfirmPaymentIntentRequest(BaseModel):
    payment_method_id: str


class CreateRefundRequest(BaseModel):
    amount_minor: Optional[int] = None
    reason: Optional[str] = None


class CreateRefundResponse(BaseModel):
    refund_id: str
    amount_minor: int
    currency: str
    status: str
    reason: Optional[str] = None


class CreateSetupIntentRequest(BaseModel):
    customer_id: str
    payment_method_types: List[str]
    metadata: Optional[Dict[str, Any]] = None


class CreateSetupIntentResponse(BaseModel):
    setup_intent_id: str
    client_secret: str


class CreatePaymentMethodRequest(BaseModel):
    customer_id: str
    payment_method_type: str
    payment_method_data: Dict[str, Any]


class PaymentMethodResponse(BaseModel):
    id: str
    brand: str
    last4: str
    exp_month: int
    exp_year: int
    customer_id: str


class PaymentMethodEligibilityRequest(BaseModel):
    payment_method_type: str
    amount_minor: int
    currency: str
    country: str


class PaymentMethodEligibilityResponse(BaseModel):
    is_eligible: bool
    requirements: List[str]
    restrictions: List[str]


class HealthCheckResponse(BaseModel):
    status: str
    gateways: Dict[str, Dict[str, Any]]
    timestamp: str


# Dependencies
async def get_payment_service() -> PaymentService:
    """Get payment service instance."""
    return PaymentService()


# Customer endpoints
@router.post("/customers", response_model=CreateCustomerResponse)
async def create_customer(
    request: CreateCustomerRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a new customer."""
    try:
        customer_id = await payment_service.create_customer(
            email=request.email,
            country=request.country,
            metadata=request.metadata
        )
        
        return CreateCustomerResponse(
            customer_id=customer_id,
            email=request.email,
            country=request.country,
            created_at=payment_service.get_customer(customer_id).created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to create customer: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")


@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get customer by ID."""
    try:
        customer = payment_service.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return customer
        
    except Exception as e:
        logger.error("Failed to get customer: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")


# Payment Intent endpoints
@router.post("/payment-intents", response_model=CreatePaymentIntentResponse)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a new payment intent."""
    try:
        payment_intent = await payment_service.create_payment_intent(
            amount_minor=request.amount_minor,
            currency=request.currency,
            customer_id=request.customer_id,
            capture_method=request.capture_method,
            confirmation_method=request.confirmation_method,
            metadata=request.metadata,
            payment_method_types=request.payment_method_types
        )
        
        return CreatePaymentIntentResponse(
            payment_intent_id=payment_intent.id,
            amount_minor=payment_intent.amount_minor,
            currency=payment_intent.currency,
            status=payment_intent.status,
            client_secret=payment_intent.client_secret,
            capture_method=payment_intent.capture_method,
            confirmation_method=payment_intent.confirmation_method
        )
        
    except Exception as e:
        logger.error("Failed to create payment intent: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create payment intent: {str(e)}")


@router.post("/payment-intents/{payment_intent_id}/confirm")
async def confirm_payment_intent(
    payment_intent_id: str,
    request: ConfirmPaymentIntentRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Confirm a payment intent."""
    try:
        payment_intent = await payment_service.confirm_payment_intent(
            payment_intent_id=payment_intent_id,
            payment_method_id=request.payment_method_id
        )
        
        return {
            "payment_intent_id": payment_intent.id,
            "status": payment_intent.status,
            "amount_minor": payment_intent.amount_minor,
            "currency": payment_intent.currency
        }
        
    except Exception as e:
        logger.error("Failed to confirm payment intent: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to confirm payment intent: {str(e)}")


@router.get("/payment-intents/{payment_intent_id}")
async def get_payment_intent(
    payment_intent_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get payment intent by ID."""
    try:
        payment_intent = await payment_service.get_payment_intent(payment_intent_id)
        if not payment_intent:
            raise HTTPException(status_code=404, detail="Payment intent not found")
        
        return {
            "payment_intent_id": payment_intent.id,
            "status": payment_intent.status,
            "amount_minor": payment_intent.amount_minor,
            "currency": payment_intent.currency,
            "capture_method": payment_intent.capture_method,
            "confirmation_method": payment_intent.confirmation_method
        }
        
    except Exception as e:
        logger.error("Failed to get payment intent: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get payment intent: {str(e)}")


@router.post("/payment-intents/{payment_intent_id}/capture")
async def capture_payment_intent(
    payment_intent_id: str,
    amount_minor: Optional[int] = Query(None, description="Amount to capture in minor units"),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Capture a payment intent."""
    try:
        charge = await payment_service.capture_payment_intent(
            payment_intent_id=payment_intent_id,
            amount_minor=amount_minor
        )
        
        return {
            "charge_id": charge.id,
            "status": charge.status,
            "amount_minor": charge.amount_minor,
            "currency": charge.currency,
            "receipt_url": charge.receipt_url
        }
        
    except Exception as e:
        logger.error("Failed to capture payment intent: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to capture payment intent: {str(e)}")


# Charge endpoints
@router.get("/charges/{charge_id}")
async def get_charge(
    charge_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get charge by ID."""
    try:
        charge = await payment_service.get_charge(charge_id)
        if not charge:
            raise HTTPException(status_code=404, detail="Charge not found")
        
        return {
            "charge_id": charge.id,
            "status": charge.status,
            "amount_minor": charge.amount_minor,
            "currency": charge.currency,
            "receipt_url": charge.receipt_url
        }
        
    except Exception as e:
        logger.error("Failed to get charge: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get charge: {str(e)}")


# Refund endpoints
@router.post("/charges/{charge_id}/refunds", response_model=CreateRefundResponse)
async def create_refund(
    charge_id: str,
    request: CreateRefundRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a refund for a charge."""
    try:
        refund = await payment_service.create_refund(
            charge_id=charge_id,
            amount_minor=request.amount_minor,
            reason=request.reason
        )
        
        return CreateRefundResponse(
            refund_id=refund.id,
            amount_minor=refund.amount_minor,
            currency=refund.currency,
            status=refund.status,
            reason=refund.reason
        )
        
    except Exception as e:
        logger.error("Failed to create refund: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create refund: {str(e)}")


# Setup Intent endpoints
@router.post("/setup-intents", response_model=CreateSetupIntentResponse)
async def create_setup_intent(
    request: CreateSetupIntentRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a setup intent for saving payment methods."""
    try:
        setup_intent_id = await payment_service.create_setup_intent(
            customer_id=request.customer_id,
            payment_method_types=request.payment_method_types,
            metadata=request.metadata
        )
        
        return CreateSetupIntentResponse(
            setup_intent_id=setup_intent_id,
            client_secret=setup_intent_id  # This should be the actual client secret
        )
        
    except Exception as e:
        logger.error("Failed to create setup intent: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create setup intent: {str(e)}")


# Payment Method endpoints
@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def create_payment_method(
    request: CreatePaymentMethodRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a payment method."""
    try:
        payment_method = await payment_service.create_payment_method(
            customer_id=request.customer_id,
            payment_method_type=request.payment_method_type,
            payment_method_data=request.payment_method_data
        )
        
        return PaymentMethodResponse(
            id=payment_method.id,
            brand=payment_method.brand,
            last4=payment_method.last4,
            exp_month=payment_method.exp_month,
            exp_year=payment_method.exp_year,
            customer_id=payment_method.customer_id
        )
        
    except Exception as e:
        logger.error("Failed to create payment method: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create payment method: {str(e)}")


@router.get("/customers/{customer_id}/payment-methods")
async def list_payment_methods(
    customer_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """List payment methods for a customer."""
    try:
        payment_methods = await payment_service.list_payment_methods(customer_id)
        
        return [
            {
                "id": pm.id,
                "brand": pm.brand,
                "last4": pm.last4,
                "exp_month": pm.exp_month,
                "exp_year": pm.exp_year
            }
            for pm in payment_methods
        ]
        
    except Exception as e:
        logger.error("Failed to list payment methods: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list payment methods: {str(e)}")


@router.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Delete a payment method."""
    try:
        success = await payment_service.delete_payment_method(payment_method_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Payment method not found")
        
        return {"deleted": True}
        
    except Exception as e:
        logger.error("Failed to delete payment method: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete payment method: {str(e)}")


# Payment Method Eligibility endpoints
@router.post("/payment-methods/eligibility", response_model=PaymentMethodEligibilityResponse)
async def check_payment_method_eligibility(
    request: PaymentMethodEligibilityRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Check if a payment method is eligible for a transaction."""
    try:
        eligibility = await payment_service.get_payment_method_eligibility(
            payment_method_type=request.payment_method_type,
            amount_minor=request.amount_minor,
            currency=request.currency,
            country=request.country
        )
        
        return PaymentMethodEligibilityResponse(
            is_eligible=eligibility["is_eligible"],
            requirements=eligibility.get("requirements", []),
            restrictions=eligibility.get("restrictions", [])
        )
        
    except Exception as e:
        logger.error("Failed to check payment method eligibility: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to check eligibility: {str(e)}")


# Health Check endpoints
@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Check the health of all payment gateways."""
    try:
        health_status = await payment_service.health_check()
        
        return HealthCheckResponse(
            status=health_status["overall_status"],
            gateways=health_status["gateways"],
            timestamp=health_status["timestamp"]
        )
        
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Webhook endpoints
@router.post("/webhooks/{gateway}")
async def process_webhook(
    gateway: str,
    payload: Dict[str, Any] = Body(...),
    headers: Dict[str, str] = Depends(lambda: {}),
    webhook_manager: WebhookManager = Depends(get_webhook_manager)
):
    """Process webhook from payment gateway."""
    try:
        # Convert headers to dict if needed
        if not isinstance(headers, dict):
            headers = dict(headers)
        
        result = await webhook_manager.process_webhook(gateway, payload, headers)
        
        return result
        
    except Exception as e:
        logger.error("Webhook processing failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


# Subscription endpoints
@router.post("/subscriptions")
async def create_subscription(
    customer_id: str = Query(..., description="Customer ID"),
    price_id: str = Query(..., description="Price ID for the subscription"),
    payment_behavior: str = Query("default_incomplete", description="Payment behavior"),
    payment_settings: Optional[Dict[str, Any]] = Body(None),
    metadata: Optional[Dict[str, Any]] = Body(None),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a subscription."""
    try:
        subscription = await payment_service.create_subscription(
            customer_id=customer_id,
            price_id=price_id,
            payment_behavior=payment_behavior,
            payment_settings=payment_settings,
            metadata=metadata
        )
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "customer_id": subscription.customer_id,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to create subscription: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@router.get("/subscriptions/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get subscription by ID."""
    try:
        subscription = await payment_service.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "customer_id": subscription.customer_id,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get subscription: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    cancel_at_period_end: bool = Query(True, description="Cancel at period end"),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Cancel a subscription."""
    try:
        subscription = await payment_service.cancel_subscription(
            subscription_id=subscription_id,
            cancel_at_period_end=cancel_at_period_end
        )
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "canceled_at": subscription.canceled_at.isoformat() if subscription.canceled_at else None
        }
        
    except Exception as e:
        logger.error("Failed to cancel subscription: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


# Invoice endpoints
@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Get invoice by ID."""
    try:
        invoice = await payment_service.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return {
            "invoice_id": invoice.id,
            "status": invoice.status,
            "amount_due": invoice.amount_due,
            "amount_paid": invoice.amount_paid,
            "currency": invoice.currency,
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None
        }
        
    except Exception as e:
        logger.error("Failed to get invoice: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get invoice: {str(e)}")


@router.post("/invoices/{invoice_id}/pay")
async def pay_invoice(
    invoice_id: str,
    payment_method_id: str = Query(..., description="Payment method ID to use"),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Pay an invoice."""
    try:
        payment_intent = await payment_service.pay_invoice(
            invoice_id=invoice_id,
            payment_method_id=payment_method_id
        )
        
        return {
            "payment_intent_id": payment_intent.id,
            "status": payment_intent.status,
            "amount_minor": payment_intent.amount_minor,
            "currency": payment_intent.currency
        }
        
    except Exception as e:
        logger.error("Failed to pay invoice: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to pay invoice: {str(e)}")
