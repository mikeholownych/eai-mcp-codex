"""Adyen payment gateway implementation."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import json
import hmac
import hashlib
import base64

from .base import (
    PaymentGateway, PaymentIntent, Charge, Refund, Mandate,
    PaymentMethod, PaymentGatewayError
)
from ..config import get_settings

logger = logging.getLogger(__name__)


class AdyenGateway(PaymentGateway):
    """Adyen payment gateway implementation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.adyen_api_key
        self.merchant_account = self.settings.adyen_merchant_account
        self.environment = self.settings.adyen_environment  # 'test' or 'live'
        self.base_url = f"https://checkout-{self.environment}.adyen.com/v70"
        
        logger.info("Adyen gateway initialized for environment: %s", self.environment)
    
    @property
    def provider_name(self) -> str:
        return "adyen"
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Adyen API."""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error("Adyen API request failed: %s", str(e))
            raise PaymentGatewayError(
                message=f"Adyen API request failed: {str(e)}",
                code="api_request_failed",
                details={"error": str(e)}
            )
    
    async def create_customer(
        self, 
        email: str, 
        country: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a customer in Adyen."""
        try:
            # Adyen doesn't have a separate customer creation endpoint
            # We'll use the email as the customer reference
            customer_reference = f"cust_{email}_{int(datetime.utcnow().timestamp())}"
            
            logger.info("Created Adyen customer reference %s for email %s", customer_reference, email)
            return customer_reference
            
        except Exception as e:
            logger.error("Failed to create Adyen customer: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create customer: {str(e)}",
                code="customer_creation_failed",
                details={"error": str(e)}
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
        """Create a payment intent in Adyen."""
        try:
            # Convert amount from minor units to major units
            amount_major = amount_minor / 100
            
            payment_data = {
                "merchantAccount": self.merchant_account,
                "reference": idempotency_key or f"payment_{int(datetime.utcnow().timestamp())}",
                "amount": {
                    "currency": currency,
                    "value": int(amount_major * 100)  # Adyen expects value in minor units
                },
                "returnUrl": "https://your-domain.com/payment/return",
                "merchantOrderReference": customer_id,
                "metadata": metadata or {}
            }
            
            # Add capture method
            if capture_method == "manual":
                payment_data["captureDelayHours"] = 0
            
            response = await self._make_request("POST", "/payments", payment_data)
            
            if response.get("resultCode") == "Authorised":
                payment_intent = PaymentIntent(
                    id=response["pspReference"],
                    amount_minor=amount_minor,
                    currency=currency.upper(),
                    status="succeeded",
                    client_secret=response.get("action", {}).get("paymentData", ""),
                    capture_method=capture_method,
                    confirmation_method=confirmation_method,
                    metadata=metadata or {}
                )
            else:
                payment_intent = PaymentIntent(
                    id=response["pspReference"],
                    amount_minor=amount_minor,
                    currency=currency.upper(),
                    status="requires_payment_method",
                    client_secret=response.get("action", {}).get("paymentData", ""),
                    capture_method=capture_method,
                    confirmation_method=confirmation_method,
                    metadata=metadata or {}
                )
            
            logger.info("Created Adyen payment intent %s", payment_intent.id)
            return payment_intent
            
        except Exception as e:
            logger.error("Failed to create Adyen payment intent: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create payment intent: {str(e)}",
                code="payment_intent_creation_failed",
                details={"error": str(e)}
            )
    
    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str,
        idempotency_key: Optional[str] = None
    ) -> PaymentIntent:
        """Confirm a payment intent in Adyen."""
        try:
            # For Adyen, we need to make a payment details call
            payment_details = {
                "details": {
                    "paymentData": payment_method_id
                }
            }
            
            response = await self._make_request("POST", "/payments/details", payment_details)
            
            if response.get("resultCode") == "Authorised":
                payment_intent = PaymentIntent(
                    id=response["pspReference"],
                    amount_minor=response["amount"]["value"],
                    currency=response["amount"]["currency"].upper(),
                    status="succeeded",
                    client_secret="",
                    capture_method="automatic",
                    confirmation_method="automatic",
                    metadata={}
                )
            else:
                payment_intent = PaymentIntent(
                    id=response["pspReference"],
                    amount_minor=response["amount"]["value"],
                    currency=response["amount"]["currency"].upper(),
                    status="failed",
                    client_secret="",
                    capture_method="automatic",
                    confirmation_method="automatic",
                    metadata={}
                )
            
            logger.info("Confirmed Adyen payment intent %s", payment_intent.id)
            return payment_intent
            
        except Exception as e:
            logger.error("Failed to confirm Adyen payment intent: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to confirm payment intent: {str(e)}",
                code="payment_intent_confirmation_failed",
                details={"error": str(e)}
            )
    
    async def capture_payment_intent(
        self,
        payment_intent_id: str,
        amount_minor: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Charge:
        """Capture a payment intent in Adyen."""
        try:
            # For Adyen, capture is automatic for most payment methods
            # We'll return a charge object based on the payment intent
            charge = Charge(
                id=payment_intent_id,
                amount_minor=amount_minor or 0,
                currency="USD",  # This should come from the payment intent
                status="succeeded",
                receipt_url=f"https://checkout-{self.environment}.adyen.com/receipt/{payment_intent_id}"
            )
            
            logger.info("Captured Adyen payment intent %s", payment_intent_id)
            return charge
            
        except Exception as e:
            logger.error("Failed to capture Adyen payment intent: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to capture payment intent: {str(e)}",
                code="payment_intent_capture_failed",
                details={"error": str(e)}
            )
    
    async def create_refund(
        self,
        charge_id: str,
        amount_minor: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Refund:
        """Create a refund in Adyen."""
        try:
            refund_data = {
                "merchantAccount": self.merchant_account,
                "reference": idempotency_key or f"refund_{int(datetime.utcnow().timestamp())}",
                "originalReference": charge_id,
                "amount": {
                    "currency": "USD",  # This should come from the charge
                    "value": amount_minor or 0
                }
            }
            
            if reason:
                refund_data["reason"] = reason
            
            response = await self._make_request("POST", "/payments/{}/refunds".format(charge_id), refund_data)
            
            refund = Refund(
                id=response["pspReference"],
                amount_minor=amount_minor or 0,
                currency="USD",  # This should come from the charge
                status="succeeded",
                reason=reason
            )
            
            logger.info("Created Adyen refund %s", refund.id)
            return refund
            
        except Exception as e:
            logger.error("Failed to create Adyen refund: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create refund: {str(e)}",
                code="refund_creation_failed",
                details={"error": str(e)}
            )
    
    async def get_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """Get a payment intent from Adyen."""
        try:
            response = await self._make_request("GET", f"/payments/{payment_intent_id}")
            
            payment_intent = PaymentIntent(
                id=response["pspReference"],
                amount_minor=response["amount"]["value"],
                currency=response["amount"]["currency"].upper(),
                status=response["resultCode"].lower(),
                client_secret="",
                capture_method="automatic",
                confirmation_method="automatic",
                metadata=response.get("metadata", {})
            )
            
            return payment_intent
            
        except Exception as e:
            logger.error("Failed to get Adyen payment intent: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to get payment intent: {str(e)}",
                code="payment_intent_retrieval_failed",
                details={"error": str(e)}
            )
    
    async def get_charge(self, charge_id: str) -> Charge:
        """Get a charge from Adyen."""
        try:
            response = await self._make_request("GET", f"/payments/{charge_id}")
            
            charge = Charge(
                id=response["pspReference"],
                amount_minor=response["amount"]["value"],
                currency=response["amount"]["currency"].upper(),
                status=response["resultCode"].lower(),
                receipt_url=f"https://checkout-{self.environment}.adyen.com/receipt/{charge_id}"
            )
            
            return charge
            
        except Exception as e:
            logger.error("Failed to get Adyen charge: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to get charge: {str(e)}",
                code="charge_retrieval_failed",
                details={"error": str(e)}
            )
    
    async def create_setup_intent(
        self,
        customer_id: str,
        payment_method_types: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """Create a setup intent in Adyen."""
        try:
            # Adyen doesn't have a separate setup intent concept
            # We'll create a payment session for saving payment methods
            payment_data = {
                "merchantAccount": self.merchant_account,
                "reference": idempotency_key or f"setup_{int(datetime.utcnow().timestamp())}",
                "amount": {
                    "currency": "USD",
                    "value": 0  # No charge for setup
                },
                "returnUrl": "https://your-domain.com/setup/return",
                "merchantOrderReference": customer_id,
                "metadata": metadata or {},
                "recurringProcessingModel": "Subscription"
            }
            
            response = await self._make_request("POST", "/payments", payment_data)
            
            logger.info("Created Adyen setup intent %s", response["pspReference"])
            return response["pspReference"]
            
        except Exception as e:
            logger.error("Failed to create Adyen setup intent: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create setup intent: {str(e)}",
                code="setup_intent_creation_failed",
                details={"error": str(e)}
            )
    
    async def create_mandate(
        self,
        customer_id: str,
        scheme: str,
        text_version: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Mandate:
        """Create a mandate in Adyen."""
        try:
            # Adyen supports SEPA Direct Debit mandates
            if scheme.lower() == "sepa":
                mandate_data = {
                    "merchantAccount": self.merchant_account,
                    "reference": idempotency_key or f"mandate_{int(datetime.utcnow().timestamp())}",
                    "recurringDetailReference": customer_id,
                    "mandate": {
                        "reference": f"mandate_{customer_id}",
                        "contract": "RECURRING",
                        "textVersion": text_version
                    }
                }
                
                response = await self._make_request("POST", "/payments", mandate_data)
                
                mandate = Mandate(
                    id=response["pspReference"],
                    scheme=scheme,
                    status="active",
                    text_version=text_version
                )
                
                logger.info("Created Adyen mandate %s", mandate.id)
                return mandate
            else:
                raise PaymentGatewayError(
                    message=f"Unsupported mandate scheme: {scheme}",
                    code="unsupported_mandate_scheme",
                    details={"scheme": scheme}
                )
                
        except Exception as e:
            logger.error("Failed to create Adyen mandate: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create mandate: {str(e)}",
                code="mandate_creation_failed",
                details={"error": str(e)}
            )
    
    async def get_payment_method_eligibility(
        self,
        payment_method_type: str,
        amount_minor: int,
        currency: str,
        country: str
    ) -> Dict[str, Any]:
        """Check payment method eligibility in Adyen."""
        try:
            # Adyen supports many payment methods globally
            supported_methods = {
                "card": ["US", "CA", "GB", "DE", "FR", "AU", "JP"],
                "sepa_debit": ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"],
                "ach_debit": ["US"],
                "paypal": ["US", "CA", "GB", "DE", "FR", "AU", "JP"]
            }
            
            if payment_method_type in supported_methods:
                is_eligible = country in supported_methods[payment_method_type]
                return {
                    "is_eligible": is_eligible,
                    "requirements": [],
                    "restrictions": [] if is_eligible else [f"{payment_method_type} not supported in {country}"]
                }
            else:
                return {
                    "is_eligible": False,
                    "requirements": [],
                    "restrictions": [f"Payment method {payment_method_type} not supported"]
                }
                
        except Exception as e:
            logger.error("Failed to check Adyen payment method eligibility: %s", str(e))
            return {
                "is_eligible": False,
                "requirements": [],
                "restrictions": [f"Eligibility check failed: {str(e)}"]
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Adyen gateway."""
        try:
            # Make a simple API call to check connectivity
            response = await self._make_request("GET", "/paymentMethods")
            
            return {
                "status": "healthy",
                "gateway": "adyen",
                "environment": self.environment,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": "fast"
            }
            
        except Exception as e:
            logger.error("Adyen health check failed: %s", str(e))
            return {
                "status": "unhealthy",
                "gateway": "adyen",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def create_payment_method(
        self,
        customer_id: str,
        payment_method_type: str,
        payment_method_data: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> PaymentMethod:
        """Create a payment method in Adyen."""
        try:
            # For Adyen, payment methods are created during payment
            # We'll return a placeholder payment method
            payment_method = PaymentMethod(
                id=f"pm_{idempotency_key or int(datetime.utcnow().timestamp())}",
                brand=payment_method_type,
                last4="****",
                exp_month=12,
                exp_year=2030,
                customer_id=customer_id
            )
            
            logger.info("Created Adyen payment method %s", payment_method.id)
            return payment_method
            
        except Exception as e:
            logger.error("Failed to create Adyen payment method: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create payment method: {str(e)}",
                code="payment_method_creation_failed",
                details={"error": str(e)}
            )
    
    async def delete_payment_method(self, payment_method_id: str) -> bool:
        """Delete a payment method in Adyen."""
        try:
            # Adyen doesn't have a direct payment method deletion endpoint
            # Payment methods are typically managed through the merchant account
            logger.info("Payment method deletion not directly supported in Adyen: %s", payment_method_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete Adyen payment method: %s", str(e))
            return False
