"""Mock payment gateway implementation for development and testing."""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random

from .base import (
    PaymentGateway, PaymentIntent, Charge, Refund, Mandate,
    PaymentMethod, PaymentGatewayError
)
from ..config import get_settings

logger = logging.getLogger(__name__)


class MockGateway(PaymentGateway):
    """Mock payment gateway for development and testing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.customers = {}
        self.payment_intents = {}
        self.charges = {}
        self.refunds = {}
        self.mandates = {}
        
        # Simulate realistic payment processing delays
        self.processing_delay_ms = 100  # 100ms delay
        
        logger.info("Mock payment gateway initialized")
    
    async def create_customer(
        self, 
        email: str, 
        country: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a mock customer."""
        customer_id = f"cus_mock_{uuid.uuid4().hex[:8]}"
        
        self.customers[customer_id] = {
            "id": customer_id,
            "email": email,
            "country": country,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }
        
        logger.info("Created mock customer %s for email %s", customer_id, email)
        return customer_id
    
    async def create_payment_intent(
        self,
        amount_minor: int,
        currency: str,
        customer_id: str,
        capture_method: str = "automatic",
        confirmation_method: str = "automatic",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> PaymentIntent:
        """Create a mock payment intent."""
        if customer_id not in self.customers:
            raise PaymentGatewayError(
                message="Customer not found",
                code="customer_not_found"
            )
        
        intent_id = f"pi_mock_{uuid.uuid4().hex[:8]}"
        client_secret = f"pi_mock_{uuid.uuid4().hex[:16]}_secret_{uuid.uuid4().hex[:16]}"
        
        # Simulate different initial states based on amount
        if amount_minor < 100:  # Less than $1.00
            status = "requires_payment_method"
        elif amount_minor > 5000:  # More than $50.00
            status = "requires_action"  # Simulate 3DS requirement
        else:
            status = "requires_confirmation"
        
        payment_intent = PaymentIntent(
            id=intent_id,
            amount_minor=amount_minor,
            currency=currency.upper(),
            status=status,
            client_secret=client_secret,
            capture_method=capture_method,
            confirmation_method=confirmation_method,
            three_ds_status=None,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        
        self.payment_intents[intent_id] = payment_intent
        
        logger.info("Created mock payment intent %s for customer %s", intent_id, customer_id)
        return payment_intent
    
    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str,
        idempotency_key: Optional[str] = None
    ) -> PaymentIntent:
        """Confirm a mock payment intent."""
        if payment_intent_id not in self.payment_intents:
            raise PaymentGatewayError(
                message="Payment intent not found",
                code="intent_not_found"
            )
        
        intent = self.payment_intents[payment_intent_id]
        
        # Simulate payment processing
        if intent.status == "requires_confirmation":
            # Simulate 3DS challenge for high amounts
            if intent.amount_minor > 5000:
                intent.status = "requires_action"
                intent.three_ds_status = "requires_action"
            else:
                intent.status = "processing"
                
                # Simulate successful processing after delay
                await self._simulate_processing_delay()
                intent.status = "succeeded"
        
        logger.info("Confirmed mock payment intent %s", payment_intent_id)
        return intent
    
    async def capture_payment_intent(
        self,
        payment_intent_id: str,
        amount_minor: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Charge:
        """Capture a mock payment intent."""
        if payment_intent_id not in self.payment_intents:
            raise PaymentGatewayError(
                message="Payment intent not found",
                code="intent_not_found"
            )
        
        intent = self.payment_intents[payment_intent_id]
        
        if intent.status != "requires_capture":
            raise PaymentGatewayError(
                message="Payment intent not in capture state",
                code="invalid_intent_state"
            )
        
        # Create a mock charge
        charge_id = f"ch_mock_{uuid.uuid4().hex[:8]}"
        charge = Charge(
            id=charge_id,
            amount_minor=amount_minor or intent.amount_minor,
            currency=intent.currency,
            status="succeeded",
            receipt_url=f"https://mock-receipt.example.com/{charge_id}",
            created_at=datetime.utcnow()
        )
        
        self.charges[charge_id] = charge
        
        # Update intent status
        intent.status = "succeeded"
        
        logger.info("Captured mock payment intent %s, charge %s", payment_intent_id, charge_id)
        return charge
    
    async def create_refund(
        self,
        charge_id: str,
        amount_minor: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Refund:
        """Create a mock refund."""
        if charge_id not in self.charges:
            raise PaymentGatewayError(
                message="Charge not found",
                code="charge_not_found"
            )
        
        charge = self.charges[charge_id]
        refund_id = f"re_mock_{uuid.uuid4().hex[:8]}"
        
        refund = Refund(
            id=refund_id,
            amount_minor=amount_minor or charge.amount_minor,
            currency=charge.currency,
            status="succeeded",
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        self.refunds[refund_id] = refund
        
        logger.info("Created mock refund %s for charge %s", refund_id, charge_id)
        return refund
    
    async def get_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """Retrieve a mock payment intent."""
        if payment_intent_id not in self.payment_intents:
            raise PaymentGatewayError(
                message="Payment intent not found",
                code="intent_not_found"
            )
        
        return self.payment_intents[payment_intent_id]
    
    async def get_charge(self, charge_id: str) -> Charge:
        """Retrieve a mock charge."""
        if charge_id not in self.charges:
            raise PaymentGatewayError(
                message="Charge not found",
                code="charge_not_found"
            )
        
        return self.charges[charge_id]
    
    async def create_setup_intent(
        self,
        customer_id: str,
        payment_method_types: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """Create a mock setup intent."""
        if customer_id not in self.customers:
            raise PaymentGatewayError(
                message="Customer not found",
                code="customer_not_found"
            )
        
        setup_intent_id = f"seti_mock_{uuid.uuid4().hex[:8]}"
        
        logger.info("Created mock setup intent %s for customer %s", setup_intent_id, customer_id)
        return setup_intent_id
    
    async def create_mandate(
        self,
        customer_id: str,
        scheme: str,
        text_version: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Mandate:
        """Create a mock mandate."""
        if customer_id not in self.customers:
            raise PaymentGatewayError(
                message="Customer not found",
                code="customer_not_found"
            )
        
        mandate_id = f"mandate_mock_{uuid.uuid4().hex[:8]}"
        
        mandate = Mandate(
            id=mandate_id,
            scheme=scheme,
            status="active",
            text_version=text_version,
            created_at=datetime.utcnow()
        )
        
        self.mandates[mandate_id] = mandate
        
        logger.info("Created mock mandate %s for customer %s", mandate_id, customer_id)
        return mandate
    
    async def get_payment_method_eligibility(
        self,
        payment_method_type: str,
        amount_minor: int,
        currency: str,
        country: str
    ) -> Dict[str, Any]:
        """Check payment method eligibility in mock mode."""
        eligibility = {
            "is_eligible": True,
            "requirements": [],
            "restrictions": []
        }
        
        # Simulate realistic eligibility checks
        if payment_method_type == "apple_pay":
            eligibility["is_eligible"] = country in ["US", "CA", "GB", "DE", "FR", "IT", "ES"]
            if not eligibility["is_eligible"]:
                eligibility["restrictions"].append("Apple Pay not available in this country")
        
        elif payment_method_type == "google_pay":
            eligibility["is_eligible"] = True
        
        elif payment_method_type == "sepa":
            sepa_countries = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
            eligibility["is_eligible"] = country in sepa_countries
            if not eligibility["is_eligible"]:
                eligibility["restrictions"].append("SEPA not available in this country")
        
        elif payment_method_type == "ach":
            eligibility["is_eligible"] = country == "US"
            if not eligibility["is_eligible"]:
                eligibility["restrictions"].append("ACH only available in US")
        
        # Simulate random eligibility issues for testing
        if random.random() < 0.1:  # 10% chance of random restriction
            eligibility["is_eligible"] = False
            eligibility["restrictions"].append("Random testing restriction")
        
        return eligibility
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a mock health check."""
        return {
            "status": "healthy",
            "provider": "mock",
            "customers_count": len(self.customers),
            "payment_intents_count": len(self.payment_intents),
            "charges_count": len(self.charges),
            "refunds_count": len(self.refunds),
            "mandates_count": len(self.mandates),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _simulate_processing_delay(self):
        """Simulate realistic payment processing delay."""
        import asyncio
        await asyncio.sleep(self.processing_delay_ms / 1000)
    
    def reset_mock_data(self):
        """Reset all mock data for testing."""
        self.customers.clear()
        self.payment_intents.clear()
        self.charges.clear()
        self.refunds.clear()
        self.mandates.clear()
        logger.info("Mock gateway data reset")
    
    def set_processing_delay(self, delay_ms: int):
        """Set the processing delay for testing."""
        self.processing_delay_ms = delay_ms
        logger.info("Mock gateway processing delay set to %dms", delay_ms)
    
    def simulate_failure_rate(self, failure_rate: float):
        """Set the failure rate for testing (0.0 to 1.0)."""
        self.failure_rate = max(0.0, min(1.0, failure_rate))
        logger.info("Mock gateway failure rate set to %.2f%%", self.failure_rate * 100)
