"""Payment API endpoints."""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from uuid import uuid4

from .service import PaymentService
from .models import Customer, PaymentIntent, Charge, Refund
from .auth import get_current_user, require_permission
from .utils import create_audit_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

# Pydantic models for API requests/responses
class CustomerCreateRequest(BaseModel):
    email: str = Field(..., description="Customer email address")
    country: str = Field(..., description="Customer country code (ISO 3166-1 alpha-2)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional customer metadata")
    preferred_gateway: Optional[str] = Field(None, description="Preferred payment gateway")

class CustomerResponse(BaseModel):
    id: str
    external_id: str
    email: str
    country: str
    created_at: str
    updated_at: str

class PaymentIntentCreateRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    amount_minor: int = Field(..., description="Amount in minor units (e.g., cents)")
    currency: str = Field(..., description="Currency code (ISO 4217)")
    capture_method: str = Field("automatic", description="Capture method: automatic or manual")
    confirmation_method: str = Field("automatic", description="Confirmation method: automatic or manual")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional payment metadata")
    preferred_gateway: Optional[str] = Field(None, description="Preferred payment gateway")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for duplicate prevention")

class PaymentIntentResponse(BaseModel):
    id: str
    status: str
    amount_minor: int
    currency: str
    capture_method: str
    confirmation_method: str
    three_ds_status: Optional[str]
    client_secret: Optional[str]
    next_action: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: str

class PaymentIntentConfirmRequest(BaseModel):
    payment_method_id: str = Field(..., description="Payment method ID")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")

class PaymentIntentCaptureRequest(BaseModel):
    amount_minor: Optional[int] = Field(None, description="Amount to capture (if different from intent)")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")

class RefundCreateRequest(BaseModel):
    amount_minor: Optional[int] = Field(None, description="Amount to refund (if different from charge)")
    reason: Optional[str] = Field(None, description="Refund reason")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")

class RefundResponse(BaseModel):
    id: str
    amount_minor: int
    currency: str
    status: str
    reason: Optional[str]
    created_at: str

class ChargeResponse(BaseModel):
    id: str
    amount_minor: int
    currency: str
    status: str
    receipt_url: Optional[str]
    created_at: str

class HealthCheckResponse(BaseModel):
    status: str
    gateways: Dict[str, Dict[str, Any]]
    timestamp: str

class PaymentMethodEligibilityRequest(BaseModel):
    payment_method_type: str = Field(..., description="Payment method type (e.g., card, sepa_debit)")
    amount_minor: int = Field(..., description="Amount in minor units")
    currency: str = Field(..., description="Currency code")
    country: str = Field(..., description="Country code")

class PaymentMethodEligibilityResponse(BaseModel):
    is_eligible: bool
    requirements: List[str]
    restrictions: List[str]
    gateway: Optional[str]


# Dependency to get payment service
def get_payment_service() -> PaymentService:
    return PaymentService()


@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    request: CustomerCreateRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new customer."""
    try:
        require_permission(current_user, "payments:customers:create")
        
        customer_id, external_id = await payment_service.create_customer(
            email=request.email,
            country=request.country,
            metadata=request.metadata,
            preferred_gateway=request.preferred_gateway
        )
        
        # Get customer details from database
        db_session = payment_service.gateway_factory.get_db_session()
        customer = db_session.query(Customer).filter(Customer.id == customer_id).first()
        
        return CustomerResponse(
            id=customer.id,
            external_id=customer.external_id,
            email=customer.email,
            country=customer.country,
            created_at=customer.created_at.isoformat(),
            updated_at=customer.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to create customer: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get customer details."""
    try:
        require_permission(current_user, "payments:customers:read")
        
        db_session = payment_service.gateway_factory.get_db_session()
        customer = db_session.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerResponse(
            id=customer.id,
            external_id=customer.external_id,
            email=customer.email,
            country=customer.country,
            created_at=customer.created_at.isoformat(),
            updated_at=customer.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get customer %s: %s", customer_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/payment-intents", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentCreateRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new payment intent."""
    try:
        require_permission(current_user, "payments:intents:create")
        
        payment_intent, db_intent_id = await payment_service.create_payment_intent(
            customer_id=request.customer_id,
            amount_minor=request.amount_minor,
            currency=request.currency,
            capture_method=request.capture_method,
            confirmation_method=request.confirmation_method,
            metadata=request.metadata,
            preferred_gateway=request.preferred_gateway,
            idempotency_key=request.idempotency_key
        )
        
        return PaymentIntentResponse(
            id=db_intent_id,
            status=payment_intent.status,
            amount_minor=payment_intent.amount_minor,
            currency=payment_intent.currency,
            capture_method=payment_intent.capture_method,
            confirmation_method=payment_intent.confirmation_method,
            three_ds_status=payment_intent.three_ds_status,
            client_secret=payment_intent.client_secret,
            next_action=payment_intent.next_action,
            metadata=payment_intent.metadata,
            created_at=payment_intent.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to create payment intent: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intents/{payment_intent_id}/confirm", response_model=PaymentIntentResponse)
async def confirm_payment_intent(
    payment_intent_id: str,
    request: PaymentIntentConfirmRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Confirm a payment intent."""
    try:
        require_permission(current_user, "payments:intents:confirm")
        
        payment_intent = await payment_service.confirm_payment_intent(
            payment_intent_id=payment_intent_id,
            payment_method_id=request.payment_method_id,
            idempotency_key=request.idempotency_key
        )
        
        # Get updated database record
        db_session = payment_service.gateway_factory.get_db_session()
        db_intent = db_session.query(PaymentIntent).filter(PaymentIntent.id == payment_intent_id).first()
        
        return PaymentIntentResponse(
            id=payment_intent_id,
            status=payment_intent.status,
            amount_minor=payment_intent.amount_minor,
            currency=payment_intent.currency,
            capture_method=payment_intent.capture_method,
            confirmation_method=payment_intent.confirmation_method,
            three_ds_status=payment_intent.three_ds_status,
            client_secret=payment_intent.client_secret,
            next_action=payment_intent.next_action,
            metadata=payment_intent.metadata,
            created_at=payment_intent.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to confirm payment intent %s: %s", payment_intent_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intents/{payment_intent_id}/capture", response_model=ChargeResponse)
async def capture_payment_intent(
    payment_intent_id: str,
    request: PaymentIntentCaptureRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Capture a payment intent."""
    try:
        require_permission(current_user, "payments:intents:capture")
        
        charge, db_charge_id = await payment_service.capture_payment_intent(
            payment_intent_id=payment_intent_id,
            amount_minor=request.amount_minor,
            idempotency_key=request.idempotency_key
        )
        
        return ChargeResponse(
            id=db_charge_id,
            amount_minor=charge.amount_minor,
            currency=charge.currency,
            status=charge.status,
            receipt_url=charge.receipt_url,
            created_at=charge.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to capture payment intent %s: %s", payment_intent_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-intents/{payment_intent_id}", response_model=PaymentIntentResponse)
async def get_payment_intent(
    payment_intent_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get payment intent details."""
    try:
        require_permission(current_user, "payments:intents:read")
        
        payment_intent = await payment_service.get_payment_intent(payment_intent_id)
        
        # Get database record for additional fields
        db_session = payment_service.gateway_factory.get_db_session()
        db_intent = db_session.query(PaymentIntent).filter(PaymentIntent.id == payment_intent_id).first()
        
        return PaymentIntentResponse(
            id=payment_intent_id,
            status=payment_intent.status,
            amount_minor=payment_intent.amount_minor,
            currency=payment_intent.currency,
            capture_method=payment_intent.capture_method,
            confirmation_method=payment_intent.confirmation_method,
            three_ds_status=payment_intent.three_ds_status,
            client_secret=payment_intent.client_secret,
            next_action=payment_intent.next_action,
            metadata=payment_intent.metadata,
            created_at=payment_intent.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to get payment intent %s: %s", payment_intent_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/charges/{charge_id}", response_model=ChargeResponse)
async def get_charge(
    charge_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get charge details."""
    try:
        require_permission(current_user, "payments:charges:read")
        
        charge = await payment_service.get_charge(charge_id)
        
        # Get database record for additional fields
        db_session = payment_service.gateway_factory.get_db_session()
        db_charge = db_session.query(Charge).filter(Charge.id == charge_id).first()
        
        return ChargeResponse(
            id=charge_id,
            amount_minor=charge.amount_minor,
            currency=charge.currency,
            status=charge.status,
            receipt_url=charge.receipt_url,
            created_at=charge.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to get charge %s: %s", charge_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/charges/{charge_id}/refunds", response_model=RefundResponse)
async def create_refund(
    charge_id: str,
    request: RefundCreateRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a refund for a charge."""
    try:
        require_permission(current_user, "payments:refunds:create")
        
        refund, db_refund_id = await payment_service.create_refund(
            charge_id=charge_id,
            amount_minor=request.amount_minor,
            reason=request.reason,
            idempotency_key=request.idempotency_key
        )
        
        return RefundResponse(
            id=db_refund_id,
            amount_minor=refund.amount_minor,
            currency=refund.currency,
            status=refund.status,
            reason=refund.reason,
            created_at=refund.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to create refund for charge %s: %s", charge_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Check payment system health."""
    try:
        require_permission(current_user, "payments:health:read")
        
        health_status = await payment_service.health_check()
        return HealthCheckResponse(**health_status)
        
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.post("/payment-methods/eligibility", response_model=PaymentMethodEligibilityResponse)
async def check_payment_method_eligibility(
    request: PaymentMethodEligibilityRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Check if a payment method is eligible for a transaction."""
    try:
        require_permission(current_user, "payments:methods:eligibility:read")
        
        eligibility = await payment_service.get_payment_method_eligibility(
            payment_method_type=request.payment_method_type,
            amount_minor=request.amount_minor,
            currency=request.currency,
            country=request.country
        )
        
        return PaymentMethodEligibilityResponse(**eligibility)
        
    except Exception as e:
        logger.error("Failed to check payment method eligibility: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/gateways")
async def list_gateways(
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List available payment gateways."""
    try:
        require_permission(current_user, "payments:gateways:read")
        
        gateways = payment_service.gateway_factory.list_gateways()
        return {
            "gateways": [
                {
                    "name": name,
                    "provider": gateway.provider_name,
                    "supported_countries": gateway.supported_countries,
                    "supported_currencies": gateway.supported_currencies,
                    "supported_payment_methods": gateway.supported_payment_methods
                }
                for name, gateway in gateways.items()
            ]
        }
        
    except Exception as e:
        logger.error("Failed to list gateways: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to list gateways")
