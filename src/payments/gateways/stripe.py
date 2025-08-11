"""Stripe payment gateway implementation."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import stripe
from stripe.error import StripeError

from .base import (
    PaymentGateway, PaymentIntent, Charge, Refund, Mandate,
    PaymentMethod, PaymentGatewayError
)
from ..config import get_settings

logger = logging.getLogger(__name__)


class StripeGateway(PaymentGateway):
    """Stripe payment gateway implementation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.stripe = stripe
        self.stripe.api_key = self.settings.stripe_secret_key
        self.stripe.api_version = self.settings.stripe_api_version
        
        # Configure Stripe with our settings
        stripe.max_network_retries = 3
        stripe.telemetry = False  # Disable telemetry for privacy
        
        logger.info("Stripe gateway initialized with API version %s", self.stripe.api_version)
    
    async def create_customer(
        self, 
        email: str, 
        country: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a customer in Stripe."""
        try:
            customer_data = {
                "email": email,
                "metadata": metadata or {}
            }
            
            # Add country if provided
            if country:
                customer_data["address"] = {"country": country}
            
            customer = stripe.Customer.create(**customer_data)
            logger.info("Created Stripe customer %s for email %s", customer.id, email)
            return customer.id
            
        except StripeError as e:
            logger.error("Failed to create Stripe customer: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create customer: {str(e)}",
                code="customer_creation_failed",
                details={"stripe_error": str(e)}
            )
    
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
        """Create a payment intent in Stripe."""
        try:
            intent_data = {
                "amount": amount_minor,
                "currency": currency.lower(),
                "customer": customer_id,
                "capture_method": capture_method,
                "confirmation_method": confirmation_method,
                "metadata": metadata or {},
                "automatic_payment_methods": {
                    "enabled": True,
                    "allow_redirects": "never"
                }
            }
            
            # Add idempotency key if provided
            if idempotency_key:
                intent_data["idempotency_key"] = idempotency_key
            
            intent = stripe.PaymentIntent.create(**intent_data)
            
            logger.info("Created Stripe payment intent %s for customer %s", intent.id, customer_id)
            
            return PaymentIntent(
                id=intent.id,
                amount_minor=intent.amount,
                currency=intent.currency.upper(),
                status=intent.status,
                client_secret=intent.client_secret,
                capture_method=intent.capture_method,
                confirmation_method=intent.confirmation_method,
                three_ds_status=getattr(intent, 'last_payment_error', {}).get('code'),
                metadata=intent.metadata,
                created_at=datetime.fromtimestamp(intent.created)
            )
            
        except StripeError as e:
            logger.error("Failed to create Stripe payment intent: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create payment intent: {str(e)}",
                code="intent_creation_failed",
                details={"stripe_error": str(e)}
            )
    
    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str,
        idempotency_key: Optional[str] = None
    ) -> PaymentIntent:
        """Confirm a payment intent with a payment method."""
        try:
            confirm_data = {
                "payment_method": payment_method_id
            }
            
            if idempotency_key:
                confirm_data["idempotency_key"] = idempotency_key
            
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **confirm_data
            )
            
            logger.info("Confirmed Stripe payment intent %s with payment method %s", 
                       payment_intent_id, payment_method_id)
            
            return PaymentIntent(
                id=intent.id,
                amount_minor=intent.amount,
                currency=intent.currency.upper(),
                status=intent.status,
                client_secret=intent.client_secret,
                capture_method=intent.capture_method,
                confirmation_method=intent.confirmation_method,
                three_ds_status=getattr(intent, 'last_payment_error', {}).get('code'),
                metadata=intent.metadata,
                created_at=datetime.fromtimestamp(intent.created)
            )
            
        except StripeError as e:
            logger.error("Failed to confirm Stripe payment intent %s: %s", payment_intent_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to confirm payment intent: {str(e)}",
                code="intent_confirmation_failed",
                details={"stripe_error": str(e)}
            )
    
    async def capture_payment_intent(
        self,
        payment_intent_id: str,
        amount_minor: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Charge:
        """Capture a payment intent (for manual capture)."""
        try:
            capture_data = {}
            
            if amount_minor:
                capture_data["amount_to_capture"] = amount_minor
            
            if idempotency_key:
                capture_data["idempotency_key"] = idempotency_key
            
            intent = stripe.PaymentIntent.capture(
                payment_intent_id,
                **capture_data
            )
            
            # Get the charge from the intent
            charge = intent.latest_charge
            if not charge:
                raise PaymentGatewayError(
                    message="No charge found after capture",
                    code="capture_no_charge"
                )
            
            logger.info("Captured Stripe payment intent %s, charge %s", payment_intent_id, charge.id)
            
            return Charge(
                id=charge.id,
                amount_minor=charge.amount,
                currency=charge.currency.upper(),
                status=charge.status,
                receipt_url=charge.receipt_url,
                created_at=datetime.fromtimestamp(charge.created)
            )
            
        except StripeError as e:
            logger.error("Failed to capture Stripe payment intent %s: %s", payment_intent_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to capture payment intent: {str(e)}",
                code="intent_capture_failed",
                details={"stripe_error": str(e)}
            )
    
    async def create_refund(
        self,
        charge_id: str,
        amount_minor: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Refund:
        """Create a refund for a charge."""
        try:
            refund_data = {
                "charge": charge_id
            }
            
            if amount_minor:
                refund_data["amount"] = amount_minor
            
            if reason:
                refund_data["reason"] = reason
            
            if idempotency_key:
                refund_data["idempotency_key"] = idempotency_key
            
            refund = stripe.Refund.create(**refund_data)
            
            logger.info("Created Stripe refund %s for charge %s", refund.id, charge_id)
            
            return Refund(
                id=refund.id,
                amount_minor=refund.amount,
                currency=refund.currency.upper(),
                status=refund.status,
                reason=refund.reason,
                created_at=datetime.fromtimestamp(refund.created)
            )
            
        except StripeError as e:
            logger.error("Failed to create Stripe refund for charge %s: %s", charge_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to create refund: {str(e)}",
                code="refund_creation_failed",
                details={"stripe_error": str(e)}
            )
    
    async def get_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """Retrieve a payment intent from Stripe."""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return PaymentIntent(
                id=intent.id,
                amount_minor=intent.amount,
                currency=intent.currency.upper(),
                status=intent.status,
                client_secret=intent.client_secret,
                capture_method=intent.capture_method,
                confirmation_method=intent.confirmation_method,
                three_ds_status=getattr(intent, 'last_payment_error', {}).get('code'),
                metadata=intent.metadata,
                created_at=datetime.fromtimestamp(intent.created)
            )
            
        except StripeError as e:
            logger.error("Failed to retrieve Stripe payment intent %s: %s", payment_intent_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to retrieve payment intent: {str(e)}",
                code="intent_retrieval_failed",
                details={"stripe_error": str(e)}
            )
    
    async def get_charge(self, charge_id: str) -> Charge:
        """Retrieve a charge from Stripe."""
        try:
            charge = stripe.Charge.retrieve(charge_id)
            
            return Charge(
                id=charge.id,
                amount_minor=charge.amount,
                currency=charge.currency.upper(),
                status=charge.status,
                receipt_url=charge.receipt_url,
                created_at=datetime.fromtimestamp(charge.created)
            )
            
        except StripeError as e:
            logger.error("Failed to retrieve Stripe charge %s: %s", charge_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to retrieve charge: {str(e)}",
                code="charge_retrieval_failed",
                details={"stripe_error": str(e)}
            )
    
    async def create_setup_intent(
        self,
        customer_id: str,
        payment_method_types: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """Create a setup intent for saving payment methods."""
        try:
            setup_data = {
                "customer": customer_id,
                "payment_method_types": payment_method_types,
                "metadata": metadata or {}
            }
            
            if idempotency_key:
                setup_data["idempotency_key"] = idempotency_key
            
            setup_intent = stripe.SetupIntent.create(**setup_data)
            
            logger.info("Created Stripe setup intent %s for customer %s", setup_intent.id, customer_id)
            return setup_intent.id
            
        except StripeError as e:
            logger.error("Failed to create Stripe setup intent: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create setup intent: {str(e)}",
                code="setup_intent_creation_failed",
                details={"stripe_error": str(e)}
            )
    
    async def create_mandate(
        self,
        customer_id: str,
        scheme: str,
        text_version: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Mandate:
        """Create a mandate for recurring payments."""
        try:
            # For Stripe, mandates are typically created as part of payment method setup
            # This is a simplified implementation
            mandate_data = {
                "customer": customer_id,
                "payment_method_types": ["sepa_debit"] if scheme == "sepa" else ["us_bank_account"],
                "metadata": {
                    **(metadata or {}),
                    "scheme": scheme,
                    "text_version": text_version
                }
            }
            
            if idempotency_key:
                mandate_data["idempotency_key"] = idempotency_key
            
            setup_intent = stripe.SetupIntent.create(**mandate_data)
            
            logger.info("Created Stripe mandate setup intent %s for customer %s", setup_intent.id, customer_id)
            
            return Mandate(
                id=setup_intent.id,
                scheme=scheme,
                status="pending",
                text_version=text_version,
                created_at=datetime.fromtimestamp(setup_intent.created)
            )
            
        except StripeError as e:
            logger.error("Failed to create Stripe mandate: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create mandate: {str(e)}",
                code="mandate_creation_failed",
                details={"stripe_error": str(e)}
            )
    
    async def get_payment_method_eligibility(
        self,
        payment_method_type: str,
        amount_minor: int,
        currency: str,
        country: str
    ) -> Dict[str, Any]:
        """Check if a payment method is eligible for a transaction."""
        try:
            # This is a simplified eligibility check
            # In production, you might want to use Stripe's PaymentMethod.attach or similar
            eligibility = {
                "is_eligible": True,
                "requirements": [],
                "restrictions": []
            }
            
            # Check Apple Pay eligibility
            if payment_method_type == "apple_pay":
                eligibility["is_eligible"] = country in ["US", "CA", "GB", "DE", "FR", "IT", "ES"]
                if not eligibility["is_eligible"]:
                    eligibility["restrictions"].append("Apple Pay not available in this country")
            
            # Check Google Pay eligibility
            elif payment_method_type == "google_pay":
                eligibility["is_eligible"] = True  # Google Pay is more widely available
            
            # Check SEPA eligibility
            elif payment_method_type == "sepa":
                sepa_countries = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
                eligibility["is_eligible"] = country in sepa_countries
                if not eligibility["is_eligible"]:
                    eligibility["restrictions"].append("SEPA not available in this country")
            
            # Check ACH eligibility
            elif payment_method_type == "ach":
                eligibility["is_eligible"] = country == "US"
                if not eligibility["is_eligible"]:
                    eligibility["restrictions"].append("ACH only available in US")
            
            return eligibility
            
        except Exception as e:
            logger.error("Failed to check payment method eligibility: %s", str(e))
            return {
                "is_eligible": False,
                "requirements": [],
                "restrictions": [f"Eligibility check failed: {str(e)}"]
            }
    
    @property
    def provider_name(self) -> str:
        """Return the name of the payment provider."""
        return "stripe"

    async def create_payment_method(
        self,
        customer_id: str,
        payment_method_type: str,
        payment_method_data: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> PaymentMethod:
        """Create a payment method in Stripe."""
        try:
            # Create payment method
            pm_data = {
                "type": payment_method_type,
                "card": payment_method_data.get("card", {}),
                "billing_details": payment_method_data.get("billing_details", {})
            }
            
            if idempotency_key:
                pm_data["idempotency_key"] = idempotency_key
            
            payment_method = stripe.PaymentMethod.create(**pm_data)
            
            # Attach to customer
            payment_method.attach(customer=customer_id)
            
            logger.info("Created Stripe payment method %s for customer %s", payment_method.id, customer_id)
            
            return PaymentMethod(
                id=payment_method.id,
                brand=payment_method.card.brand if payment_method.card else None,
                last4=payment_method.card.last4 if payment_method.card else None,
                exp_month=payment_method.card.exp_month if payment_method.card else None,
                exp_year=payment_method.card.exp_year if payment_method.card else None,
                customer_id=customer_id,
                mandate_id=None  # Stripe doesn't use mandates for cards
            )
            
        except StripeError as e:
            logger.error("Failed to create Stripe payment method: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create payment method: {str(e)}",
                code="payment_method_creation_failed",
                details={"stripe_error": str(e)}
            )

    async def delete_payment_method(self, payment_method_id: str) -> bool:
        """Delete a payment method in Stripe."""
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            payment_method.detach()
            
            logger.info("Deleted Stripe payment method %s", payment_method_id)
            return True
            
        except StripeError as e:
            logger.error("Failed to delete Stripe payment method %s: %s", payment_method_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to delete payment method: {str(e)}",
                code="payment_method_deletion_failed",
                details={"stripe_error": str(e)}
            )

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the Stripe gateway."""
        try:
            # Test Stripe API connectivity
            account = stripe.Account.retrieve()
            
            return {
                "status": "healthy",
                "provider": "stripe",
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "capabilities": account.capabilities,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except StripeError as e:
            logger.error("Stripe health check failed: %s", str(e))
            return {
                "status": "unhealthy",
                "provider": "stripe",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("Unexpected error during Stripe health check: %s", str(e))
            return {
                "status": "error",
                "provider": "stripe",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
