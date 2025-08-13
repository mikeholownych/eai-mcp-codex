"""Payment service main application."""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import sqlalchemy as sa
from sqlalchemy.orm import Session

from .config import get_settings
from .gateways.base import PaymentGateway, PaymentGatewayError
from .gateways.stripe import StripeGateway
from .gateways.mock import MockGateway
from .models import (
    Base, Customer, PaymentIntent, Charge, Refund, 
    WebhookEvent, AuditLog, PaymentMethod, Mandate, SetupIntent
)
from .database import get_db, engine
from .webhooks import StripeWebhookHandler
from .utils import create_audit_log

logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Global gateway instance
gateway: Optional[PaymentGateway] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global gateway
    
    # Initialize payment gateway based on environment
    settings = get_settings()
    if settings.payment_provider == "stripe":
        gateway = StripeGateway()
        logger.info("Initialized Stripe payment gateway")
    else:
        gateway = MockGateway()
        logger.info("Initialized Mock payment gateway")
    
    yield
    
    # Cleanup
    if gateway:
        logger.info("Shutting down payment gateway")


# Create FastAPI app
app = FastAPI(
    title="Payment Service",
    description="Production-grade payment processing service with Stripe integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses
class CustomerCreateRequest(BaseModel):
    email: str = Field(..., description="Customer email address")
    country: str = Field(..., description="Customer country code (ISO 3166-1 alpha-2)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional customer metadata")
    
    @validator('country')
    def validate_country(cls, v):
        if len(v) != 2:
            raise ValueError('Country must be a 2-character ISO code')
        return v.upper()


class CustomerResponse(BaseModel):
    id: str
    external_id: str
    email: str
    country: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentIntentCreateRequest(BaseModel):
    amount_minor: int = Field(..., gt=0, description="Amount in minor units (e.g., cents)")
    currency: str = Field(..., description="Currency code (ISO 4217)")
    customer_id: str = Field(..., description="Customer ID")
    capture_method: str = Field("automatic", description="When to capture payment")
    confirmation_method: str = Field("automatic", description="How to confirm payment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('currency')
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError('Currency must be a 3-character ISO code')
        return v.upper()
    
    @validator('capture_method')
    def validate_capture_method(cls, v):
        if v not in ["automatic", "manual"]:
            raise ValueError('Capture method must be "automatic" or "manual"')
        return v
    
    @validator('confirmation_method')
    def validate_confirmation_method(cls, v):
        if v not in ["automatic", "manual"]:
            raise ValueError('Confirmation method must be "automatic" or "manual"')
        return v


class PaymentIntentResponse(BaseModel):
    id: str
    provider_id: str
    amount_minor: int
    currency: str
    status: str
    client_secret: str
    capture_method: str
    confirmation_method: str
    three_ds_status: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaymentIntentConfirmRequest(BaseModel):
    payment_method_id: str = Field(..., description="Payment method ID")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")


class RefundCreateRequest(BaseModel):
    amount_minor: Optional[int] = Field(None, gt=0, description="Amount to refund (partial refund)")
    reason: Optional[str] = Field(None, description="Reason for refund")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")


class HealthCheckResponse(BaseModel):
    status: str
    provider: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# New models for payment method management
class PaymentMethodCreateRequest(BaseModel):
    payment_method_type: str = Field(..., description="Type of payment method (card, sepa_debit, etc.)")
    payment_method_data: Dict[str, Any] = Field(..., description="Payment method specific data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PaymentMethodResponse(BaseModel):
    id: str
    provider: str
    brand: Optional[str]
    last4: Optional[str]
    exp_month: Optional[int]
    exp_year: Optional[int]
    customer_id: str
    mandate_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SetupIntentCreateRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    payment_method_types: List[str] = Field(..., description="List of payment method types")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SetupIntentResponse(BaseModel):
    id: str
    provider_id: str
    customer_id: str
    status: str
    client_secret: str
    payment_method_types: List[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MandateCreateRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    scheme: str = Field(..., description="Mandate scheme (sepa, ach, faster_payments)")
    text_version: str = Field(..., description="Mandate text version")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class MandateResponse(BaseModel):
    id: str
    provider_mandate_id: str
    scheme: str
    status: str
    text_version: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentMethodEligibilityRequest(BaseModel):
    payment_method_type: str = Field(..., description="Type of payment method")
    amount_minor: int = Field(..., gt=0, description="Amount in minor units")
    currency: str = Field(..., description="Currency code")
    country: str = Field(..., description="Country code")


class PaymentMethodEligibilityResponse(BaseModel):
    eligible: bool
    requirements: List[str]
    restrictions: List[str]
    fees: Optional[Dict[str, Any]]
    processing_time: Optional[str]


# Dependency to get the payment gateway
def get_payment_gateway() -> PaymentGateway:
    if not gateway:
        raise HTTPException(status_code=503, detail="Payment gateway not initialized")
    return gateway


# API Routes
@app.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer(
    request: CustomerCreateRequest,
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Create a new customer."""
    try:
        # Check if customer already exists
        existing_customer = db.query(Customer).filter(
            Customer.email == request.email
        ).first()
        
        if existing_customer:
            return CustomerResponse.from_orm(existing_customer)
        
        # Create customer in payment provider
        external_id = await payment_gateway.create_customer(
            email=request.email,
            country=request.country,
            metadata=request.metadata
        )
        
        # Create customer in database
        customer = Customer(
            external_id=external_id,
            email=request.email,
            country=request.country
        )
        
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="customer_created",
            resource_type="customer",
            resource_id=str(customer.id),
            metadata={"email": request.email, "country": request.country}
        )
        
        logger.info("Created customer %s for email %s", customer.id, request.email)
        return CustomerResponse.from_orm(customer)
        
    except PaymentGatewayError as e:
        logger.error("Failed to create customer: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error creating customer: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """Get customer by ID."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return CustomerResponse.from_orm(customer)


@app.post("/payment-intents", response_model=PaymentIntentResponse, status_code=201)
async def create_payment_intent(
    request: PaymentIntentCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Create a new payment intent."""
    try:
        # Check idempotency
        existing_intent = db.query(PaymentIntent).filter(
            PaymentIntent.idempotency_key == idempotency_key
        ).first()
        
        if existing_intent:
            logger.info("Returning existing payment intent for idempotency key %s", idempotency_key)
            return PaymentIntentResponse.from_orm(existing_intent)
        
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Create payment intent in payment provider
        intent = await payment_gateway.create_payment_intent(
            amount_minor=request.amount_minor,
            currency=request.currency,
            customer_id=customer.external_id,
            capture_method=request.capture_method,
            confirmation_method=request.confirmation_method,
            metadata=request.metadata,
            idempotency_key=idempotency_key
        )
        
        # Create payment intent in database
        db_intent = PaymentIntent(
            provider_id=intent.id,
            customer_id=request.customer_id,
            amount_minor=intent.amount_minor,
            currency=intent.currency,
            status=intent.status,
            capture_method=intent.capture_method,
            confirmation_method=intent.confirmation_method,
            three_ds_status=intent.three_ds_status,
            idempotency_key=idempotency_key,
            metadata=intent.metadata
        )
        
        db.add(db_intent)
        db.commit()
        db.refresh(db_intent)
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="payment_intent_created",
            resource_type="payment_intent",
            resource_id=str(db_intent.id),
            metadata={
                "amount": request.amount_minor,
                "currency": request.currency,
                "customer_id": request.customer_id
            }
        )
        
        logger.info("Created payment intent %s for customer %s", db_intent.id, request.customer_id)
        return PaymentIntentResponse.from_orm(db_intent)
        
    except PaymentGatewayError as e:
        logger.error("Failed to create payment intent: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error creating payment intent: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/payment-intents/{intent_id}/confirm", response_model=PaymentIntentResponse)
async def confirm_payment_intent(
    intent_id: str,
    request: PaymentIntentConfirmRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Confirm a payment intent."""
    try:
        # Get payment intent from database
        db_intent = db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
        if not db_intent:
            raise HTTPException(status_code=404, detail="Payment intent not found")
        
        # Confirm payment intent in payment provider
        intent = await payment_gateway.confirm_payment_intent(
            payment_intent_id=db_intent.provider_id,
            payment_method_id=request.payment_method_id,
            idempotency_key=idempotency_key
        )
        
        # Update database
        db_intent.status = intent.status
        db_intent.three_ds_status = intent.three_ds_status
        db_intent.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_intent)
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="payment_intent_confirmed",
            resource_type="payment_intent",
            resource_id=str(db_intent.id),
            metadata={
                "payment_method_id": request.payment_method_id,
                "new_status": intent.status
            }
        )
        
        logger.info("Confirmed payment intent %s", intent_id)
        return PaymentIntentResponse.from_orm(db_intent)
        
    except PaymentGatewayError as e:
        logger.error("Failed to confirm payment intent %s: %s", intent_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error confirming payment intent: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/payment-intents/{intent_id}", response_model=PaymentIntentResponse)
async def get_payment_intent(
    intent_id: str,
    db: Session = Depends(get_db)
):
    """Get payment intent by ID."""
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    
    return PaymentIntentResponse.from_orm(intent)


@app.post("/payment-intents/{intent_id}/capture")
async def capture_payment_intent(
    intent_id: str,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Capture a payment intent (manual capture only)."""
    try:
        # Get payment intent from database
        db_intent = db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
        if not db_intent:
            raise HTTPException(status_code=404, detail="Payment intent not found")
        
        if db_intent.capture_method != "manual":
            raise HTTPException(status_code=400, detail="Payment intent is not configured for manual capture")
        
        if db_intent.status != "requires_capture":
            raise HTTPException(status_code=400, detail="Payment intent is not in capture state")
        
        # Parse request body for partial capture
        body = await request.json()
        amount_minor = body.get("amount_minor")
        
        # Capture payment intent in payment provider
        charge = await payment_gateway.capture_payment_intent(
            payment_intent_id=db_intent.provider_id,
            amount_minor=amount_minor,
            idempotency_key=idempotency_key
        )
        
        # Create charge in database
        db_charge = Charge(
            payment_intent_id=intent_id,
            provider_charge_id=charge.id,
            status=charge.status,
            receipt_url=charge.receipt_url
        )
        
        db.add(db_charge)
        
        # Update payment intent status
        db_intent.status = "succeeded"
        db_intent.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="payment_intent_captured",
            resource_type="payment_intent",
            resource_id=str(db_intent.id),
            metadata={
                "charge_id": charge.id,
                "amount_captured": amount_minor or db_intent.amount_minor
            }
        )
        
        logger.info("Captured payment intent %s, charge %s", intent_id, charge.id)
        return {"status": "success", "charge_id": charge.id}
        
    except PaymentGatewayError as e:
        logger.error("Failed to capture payment intent %s: %s", intent_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error capturing payment intent: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/charges/{charge_id}/refunds")
async def create_refund(
    charge_id: str,
    request: RefundCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Create a refund for a charge."""
    try:
        # Get charge from database
        charge = db.query(Charge).filter(Charge.id == charge_id).first()
        if not charge:
            raise HTTPException(status_code=404, detail="Charge not found")
        
        # Create refund in payment provider
        refund = await payment_gateway.create_refund(
            charge_id=charge.provider_charge_id,
            amount_minor=request.amount_minor,
            reason=request.reason,
            idempotency_key=idempotency_key
        )
        
        # Create refund in database
        db_refund = Refund(
            charge_id=charge_id,
            provider_refund_id=refund.id,
            amount_minor=refund.amount_minor,
            status=refund.status,
            reason=refund.reason
        )
        
        db.add(db_refund)
        db.commit()
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="refund_created",
            resource_type="refund",
            resource_id=str(db_refund.id),
            metadata={
                "charge_id": charge_id,
                "amount": refund.amount_minor,
                "reason": refund.reason
            }
        )
        
        logger.info("Created refund %s for charge %s", refund.id, charge_id)
        return {"status": "success", "refund_id": refund.id}
        
    except PaymentGatewayError as e:
        logger.error("Failed to create refund for charge %s: %s", charge_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error creating refund: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Health check endpoint."""
    try:
        health_status = await payment_gateway.health_check()
        return HealthCheckResponse(
            status=health_status["status"],
            provider=health_status["provider"],
            timestamp=health_status["timestamp"],
            details=health_status
        )
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        return HealthCheckResponse(
            status="unhealthy",
            provider="unknown",
            timestamp=datetime.utcnow().isoformat(),
            details={"error": str(e)}
        )


# Payment Method Management Endpoints
@app.post("/customers/{customer_id}/payment-methods", response_model=PaymentMethodResponse, status_code=201)
async def create_payment_method(
    customer_id: str,
    request: PaymentMethodCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Create a new payment method for a customer."""
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Create payment method via gateway
        payment_method_data = await payment_gateway.create_payment_method(
            customer_id=customer_id,
            payment_method_type=request.payment_method_type,
            payment_method_data=request.payment_method_data,
            idempotency_key=idempotency_key
        )
        
        # Create database record
        db_payment_method = PaymentMethod(
            id=str(uuid.uuid4()),
            provider=payment_gateway.provider_name,
            pm_token=payment_method_data.id,
            brand=payment_method_data.brand,
            last4=payment_method_data.last4,
            exp_month=payment_method_data.exp_month,
            exp_year=payment_method_data.exp_year,
            customer_id=customer_id,
            mandate_id=payment_method_data.mandate_id
        )
        
        db.add(db_payment_method)
        db.commit()
        db.refresh(db_payment_method)
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="payment_method_created",
            resource_type="payment_method",
            resource_id=db_payment_method.id,
            metadata={"customer_id": customer_id, "type": request.payment_method_type}
        )
        
        return db_payment_method
        
    except PaymentGatewayError as e:
        logger.error(f"Payment gateway error creating payment method: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating payment method: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/customers/{customer_id}/payment-methods", response_model=List[PaymentMethodResponse])
async def list_customer_payment_methods(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """List all payment methods for a customer."""
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    payment_methods = db.query(PaymentMethod).filter(
        PaymentMethod.customer_id == customer_id
    ).all()
    
    return payment_methods


@app.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: str,
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Delete a payment method."""
    try:
        payment_method = db.query(PaymentMethod).filter(
            PaymentMethod.id == payment_method_id
        ).first()
        
        if not payment_method:
            raise HTTPException(status_code=404, detail="Payment method not found")
        
        # Delete from gateway
        await payment_gateway.delete_payment_method(payment_method.pm_token)
        
        # Delete from database
        db.delete(payment_method)
        db.commit()
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="payment_method_deleted",
            resource_type="payment_method",
            resource_id=payment_method_id,
            metadata={"customer_id": payment_method.customer_id}
        )
        
        return {"message": "Payment method deleted successfully"}
        
    except PaymentGatewayError as e:
        logger.error(f"Payment gateway error deleting payment method: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting payment method: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# Setup Intent Endpoints
@app.post("/setup-intents", response_model=SetupIntentResponse, status_code=201)
async def create_setup_intent(
    request: SetupIntentCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Create a setup intent for saving payment methods."""
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Create setup intent via gateway
        setup_intent_id = await payment_gateway.create_setup_intent(
            customer_id=request.customer_id,
            payment_method_types=request.payment_method_types,
            metadata=request.metadata,
            idempotency_key=idempotency_key
        )
        
        # Create database record
        db_setup_intent = SetupIntent(
            id=str(uuid.uuid4()),
            provider_id=setup_intent_id,
            customer_id=request.customer_id,
            status="requires_payment_method",
            client_secret=setup_intent_id,  # This should be the actual client secret
            payment_method_types=request.payment_method_types,
            metadata=request.metadata
        )
        
        db.add(db_setup_intent)
        db.commit()
        db.refresh(db_setup_intent)
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="setup_intent_created",
            resource_type="setup_intent",
            resource_id=db_setup_intent.id,
            metadata={"customer_id": request.customer_id}
        )
        
        return db_setup_intent
        
    except PaymentGatewayError as e:
        logger.error(f"Payment gateway error creating setup intent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating setup intent: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# Mandate Management Endpoints
@app.post("/mandates", response_model=MandateResponse, status_code=201)
async def create_mandate(
    request: MandateCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Create a mandate for recurring payments."""
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Create mandate via gateway
        mandate_data = await payment_gateway.create_mandate(
            customer_id=request.customer_id,
            scheme=request.scheme,
            text_version=request.text_version,
            metadata=request.metadata,
            idempotency_key=idempotency_key
        )
        
        # Create database record
        db_mandate = Mandate(
            id=str(uuid.uuid4()),
            provider_mandate_id=mandate_data.id,
            scheme=request.scheme,
            status=mandate_data.status,
            text_version=request.text_version
        )
        
        db.add(db_mandate)
        db.commit()
        db.refresh(db_mandate)
        
        # Create audit log
        await create_audit_log(
            db=db,
            actor="system",
            action="mandate_created",
            resource_type="mandate",
            resource_id=db_mandate.id,
            metadata={"customer_id": request.customer_id, "scheme": request.scheme}
        )
        
        return db_mandate
        
    except PaymentGatewayError as e:
        logger.error(f"Payment gateway error creating mandate: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating mandate: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# Payment Method Eligibility Endpoint
@app.post("/payment-methods/eligibility", response_model=PaymentMethodEligibilityResponse)
async def check_payment_method_eligibility(
    request: PaymentMethodEligibilityRequest,
    payment_gateway: PaymentGateway = Depends(get_payment_gateway)
):
    """Check if a payment method is eligible for a given transaction."""
    try:
        eligibility_data = await payment_gateway.get_payment_method_eligibility(
            payment_method_type=request.payment_method_type,
            amount_minor=request.amount_minor,
            currency=request.currency,
            country=request.country
        )
        
        return PaymentMethodEligibilityResponse(
            eligible=eligibility_data.get("eligible", False),
            requirements=eligibility_data.get("requirements", []),
            restrictions=eligibility_data.get("restrictions", []),
            fees=eligibility_data.get("fees"),
            processing_time=eligibility_data.get("processing_time")
        )
        
    except PaymentGatewayError as e:
        logger.error(f"Payment gateway error checking eligibility: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking payment method eligibility: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Webhook endpoints
@app.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhooks."""
    try:
        # Get raw body for signature verification
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Process webhook in background
        background_tasks.add_task(
            StripeWebhookHandler(db).process_webhook,
            body,
            signature
        )
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error("Webhook processing failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Webhook processing failed")


# Error handlers
@app.exception_handler(PaymentGatewayError)
async def payment_gateway_error_handler(request: Request, exc: PaymentGatewayError):
    """Handle payment gateway errors."""
    logger.error("Payment gateway error: %s", str(exc))
    return JSONResponse(
        status_code=400,
        content={
            "error": "payment_error",
            "message": str(exc),
            "code": exc.code,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    """Handle general errors."""
    logger.error("Unexpected error: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Internal server error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
