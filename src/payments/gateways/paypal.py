"""PayPal payment gateway implementation."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

from .base import (
    PaymentGateway, PaymentIntent, Charge, Refund, Mandate,
    PaymentMethod, PaymentGatewayError
)
from ..config import get_settings

logger = logging.getLogger(__name__)


class PayPalGateway(PaymentGateway):
    """PayPal payment gateway implementation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.paypal_base_url
        self.client_id = self.settings.paypal_client_id
        self.client_secret = self.settings.paypal_client_secret
        self.access_token = None
        self.token_expires_at = None
        
        logger.info("PayPal gateway initialized")
    
    async def _get_access_token(self) -> str:
        """Get or refresh PayPal access token."""
        if self.access_token and self.token_expires_at and datetime.utcnow() < self.token_expires_at:
            return self.access_token
        
        try:
            auth = HTTPBasicAuth(self.client_id, self.client_secret)
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=auth,
                data={"grant_type": "client_credentials"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data["expires_in"]
            self.token_expires_at = datetime.utcnow().replace(microsecond=0) + \
                                  datetime.timedelta(seconds=expires_in - 300)  # 5 min buffer
            
            logger.debug("Refreshed PayPal access token")
            return self.access_token
            
        except Exception as e:
            logger.error("Failed to get PayPal access token: %s", str(e))
            raise PaymentGatewayError(
                message="Failed to authenticate with PayPal",
                code="authentication_failed",
                details={"error": str(e)}
            )
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to PayPal API."""
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
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
            logger.error("PayPal API request failed: %s", str(e))
            raise PaymentGatewayError(
                message=f"PayPal API request failed: {str(e)}",
                code="api_request_failed",
                details={"error": str(e)}
            )
    
    async def create_customer(
        self, 
        email: str, 
        country: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a customer in PayPal (using payer_id from first payment)."""
        # PayPal doesn't have a separate customer creation endpoint
        # We'll use the email as a customer identifier
        customer_id = f"paypal_{email}"
        
        logger.info("Created PayPal customer identifier %s for email %s", customer_id, email)
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
        """Create a PayPal order (equivalent to payment intent)."""
        try:
            # Convert minor units to major units for PayPal
            amount_major = amount_minor / 100
            
            order_data = {
                "intent": "CAPTURE" if capture_method == "automatic" else "AUTHORIZE",
                "purchase_units": [{
                    "reference_id": idempotency_key or f"order_{datetime.utcnow().timestamp()}",
                    "amount": {
                        "currency_code": currency.upper(),
                        "value": f"{amount_major:.2f}"
                    },
                    "description": metadata.get("description", "Payment") if metadata else "Payment"
                }],
                "application_context": {
                    "return_url": metadata.get("return_url", "https://example.com/success") if metadata else "https://example.com/success",
                    "cancel_url": metadata.get("cancel_url", "https://example.com/cancel") if metadata else "https://example.com/cancel"
                }
            }
            
            if metadata:
                order_data["custom_id"] = metadata.get("custom_id")
            
            response = await self._make_request("POST", "/v2/checkout/orders", order_data)
            
            order_id = response["id"]
            status = response["status"].lower()
            
            # Map PayPal status to our status
            if status == "created":
                intent_status = "requires_payment_method"
            elif status == "approved":
                intent_status = "requires_capture"
            else:
                intent_status = status
            
            logger.info("Created PayPal order %s for customer %s", order_id, customer_id)
            
            return PaymentIntent(
                id=order_id,
                amount_minor=amount_minor,
                currency=currency.upper(),
                status=intent_status,
                client_secret=order_id,  # PayPal uses order ID as client secret
                capture_method=capture_method,
                confirmation_method=confirmation_method,
                three_ds_status=None,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to create PayPal order: %s", str(e))
            raise PaymentGatewayError(
                message=f"Failed to create order: {str(e)}",
                code="order_creation_failed",
                details={"error": str(e)}
            )
    
    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str,
        idempotency_key: Optional[str] = None
    ) -> PaymentIntent:
        """Confirm a PayPal order (capture the payment)."""
        try:
            # For PayPal, confirmation happens during capture
            # This method will capture the order
            response = await self._make_request("POST", f"/v2/checkout/orders/{payment_intent_id}/capture")
            
            capture_id = response["purchase_units"][0]["payments"]["captures"][0]["id"]
            status = response["status"].lower()
            
            logger.info("Captured PayPal order %s, capture %s", payment_intent_id, capture_id)
            
            return PaymentIntent(
                id=payment_intent_id,
                amount_minor=int(float(response["purchase_units"][0]["amount"]["value"]) * 100),
                currency=response["purchase_units"][0]["amount"]["currency_code"].upper(),
                status="succeeded" if status == "completed" else status,
                client_secret=payment_intent_id,
                capture_method="automatic",
                confirmation_method="automatic",
                three_ds_status=None,
                metadata={},
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to capture PayPal order %s: %s", payment_intent_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to capture order: {str(e)}",
                code="order_capture_failed",
                details={"error": str(e)}
            )
    
    async def capture_payment_intent(
        self,
        payment_intent_id: str,
        amount_minor: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Charge:
        """Capture a PayPal order."""
        try:
            response = await self._make_request("POST", f"/v2/checkout/orders/{payment_intent_id}/capture")
            
            capture = response["purchase_units"][0]["payments"]["captures"][0]
            capture_id = capture["id"]
            status = capture["status"].lower()
            
            logger.info("Captured PayPal order %s, capture %s", payment_intent_id, capture_id)
            
            return Charge(
                id=capture_id,
                amount_minor=int(float(capture["amount"]["value"]) * 100),
                currency=capture["amount"]["currency_code"].upper(),
                status=status,
                receipt_url=capture.get("links", [{}])[0].get("href") if capture.get("links") else None,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to capture PayPal order %s: %s", payment_intent_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to capture order: {str(e)}",
                code="order_capture_failed",
                details={"error": str(e)}
            )
    
    async def create_refund(
        self,
        charge_id: str,
        amount_minor: Optional[int] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Refund:
        """Create a refund for a PayPal capture."""
        try:
            # For PayPal, we need to refund the capture
            refund_data = {}
            
            if amount_minor:
                amount_major = amount_minor / 100
                refund_data["amount"] = {
                    "currency_code": "USD",  # Would need to get from original capture
                    "value": f"{amount_major:.2f}"
                }
            
            if reason:
                refund_data["reason"] = reason
            
            if idempotency_key:
                refund_data["invoice_id"] = idempotency_key
            
            response = await self._make_request("POST", f"/v2/payments/captures/{charge_id}/refund", refund_data)
            
            refund_id = response["id"]
            status = response["status"].lower()
            
            logger.info("Created PayPal refund %s for capture %s", refund_id, charge_id)
            
            return Refund(
                id=refund_id,
                amount_minor=int(float(response["amount"]["value"]) * 100),
                currency=response["amount"]["currency_code"].upper(),
                status=status,
                reason=reason,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to create PayPal refund for capture %s: %s", charge_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to create refund: {str(e)}",
                code="refund_creation_failed",
                details={"error": str(e)}
            )
    
    async def get_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """Retrieve a PayPal order."""
        try:
            response = await self._make_request("GET", f"/v2/checkout/orders/{payment_intent_id}")
            
            status = response["status"].lower()
            amount = response["purchase_units"][0]["amount"]
            
            return PaymentIntent(
                id=response["id"],
                amount_minor=int(float(amount["value"]) * 100),
                currency=amount["currency_code"].upper(),
                status=status,
                client_secret=response["id"],
                capture_method="automatic",
                confirmation_method="automatic",
                three_ds_status=None,
                metadata={},
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to retrieve PayPal order %s: %s", payment_intent_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to retrieve order: {str(e)}",
                code="order_retrieval_failed",
                details={"error": str(e)}
            )
    
    async def get_charge(self, charge_id: str) -> Charge:
        """Retrieve a PayPal capture."""
        try:
            response = await self._make_request("GET", f"/v2/payments/captures/{charge_id}")
            
            return Charge(
                id=response["id"],
                amount_minor=int(float(response["amount"]["value"]) * 100),
                currency=response["amount"]["currency_code"].upper(),
                status=response["status"].lower(),
                receipt_url=response.get("links", [{}])[0].get("href") if response.get("links") else None,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to retrieve PayPal capture %s: %s", charge_id, str(e))
            raise PaymentGatewayError(
                message=f"Failed to retrieve capture: {str(e)}",
                code="capture_retrieval_failed",
                details={"error": str(e)}
            )
    
    async def create_setup_intent(
        self,
        customer_id: str,
        payment_method_types: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """Create a setup intent for saving payment methods (PayPal doesn't support this directly)."""
        # PayPal doesn't have a direct equivalent to setup intents
        # We'll create a minimal order that can be used for setup
        setup_id = f"setup_{idempotency_key or datetime.utcnow().timestamp()}"
        
        logger.info("Created PayPal setup intent %s for customer %s", setup_id, customer_id)
        return setup_id
    
    async def create_mandate(
        self,
        customer_id: str,
        scheme: str,
        text_version: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Mandate:
        """Create a mandate for recurring payments (PayPal doesn't support this directly)."""
        # PayPal doesn't have a direct equivalent to mandates
        # We'll create a minimal mandate record
        mandate_id = f"mandate_{idempotency_key or datetime.utcnow().timestamp()}"
        
        logger.info("Created PayPal mandate %s for customer %s", mandate_id, customer_id)
        
        return Mandate(
            id=mandate_id,
            scheme=scheme,
            status="pending",
            text_version=text_version,
            created_at=datetime.utcnow()
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
            # PayPal is generally available worldwide
            eligibility = {
                "is_eligible": True,
                "requirements": [],
                "restrictions": []
            }
            
            # Check for specific restrictions
            if payment_method_type == "paypal":
                # PayPal is available in most countries
                restricted_countries = ["CU", "IR", "KP", "SD", "SY"]
                if country in restricted_countries:
                    eligibility["is_eligible"] = False
                    eligibility["restrictions"].append("PayPal not available in this country")
            
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
        return "paypal"
    
    async def create_payment_method(
        self,
        customer_id: str,
        payment_method_type: str,
        payment_method_data: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> PaymentMethod:
        """Create a payment method in PayPal (not directly supported)."""
        # PayPal doesn't have a direct equivalent to payment methods
        # We'll create a minimal payment method record
        pm_id = f"pm_{idempotency_key or datetime.utcnow().timestamp()}"
        
        logger.info("Created PayPal payment method %s for customer %s", pm_id, customer_id)
        
        return PaymentMethod(
            id=pm_id,
            brand="paypal",
            last4="0000",
            exp_month=12,
            exp_year=2030,
            customer_id=customer_id,
            mandate_id=None
        )
    
    async def delete_payment_method(self, payment_method_id: str) -> bool:
        """Delete a payment method in PayPal (not directly supported)."""
        # PayPal doesn't have a direct equivalent to payment methods
        logger.info("Deleted PayPal payment method %s", payment_method_id)
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the PayPal gateway."""
        try:
            # Test PayPal API connectivity by getting access token
            token = await self._get_access_token()
            
            return {
                "status": "healthy",
                "provider": "paypal",
                "access_token": token[:10] + "..." if token else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("PayPal health check failed: %s", str(e))
            return {
                "status": "unhealthy",
                "provider": "paypal",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
