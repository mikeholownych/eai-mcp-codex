"""Payment gateway factory for creating and managing payment gateways."""

import logging
from typing import Dict, Type, Optional, Any
from .base import PaymentGateway
from .stripe import StripeGateway
from .paypal import PayPalGateway
from .adyen import AdyenGateway
from .mock import MockGateway
from ..config import get_settings
from datetime import datetime

logger = logging.getLogger(__name__)


class PaymentGatewayFactory:
    """Factory for creating payment gateway instances."""
    
    _gateways: Dict[str, Type[PaymentGateway]] = {
        "stripe": StripeGateway,
        "paypal": PayPalGateway,
        "adyen": AdyenGateway,
        "mock": MockGateway,
    }
    
    _instances: Dict[str, PaymentGateway] = {}
    
    @classmethod
    def register_gateway(cls, name: str, gateway_class: Type[PaymentGateway]) -> None:
        """Register a new payment gateway class."""
        cls._gateways[name] = gateway_class
        logger.info("Registered payment gateway: %s", name)
    
    @classmethod
    def get_gateway(cls, name: str) -> PaymentGateway:
        """Get or create a payment gateway instance."""
        if name not in cls._instances:
            if name not in cls._gateways:
                raise ValueError(f"Unknown payment gateway: {name}")
            
            gateway_class = cls._gateways[name]
            cls._instances[name] = gateway_class()
            logger.info("Created payment gateway instance: %s", name)
        
        return cls._instances[name]
    
    @classmethod
    def get_available_gateways(cls) -> list[str]:
        """Get list of available payment gateway names."""
        return list(cls._gateways.keys())
    
    @classmethod
    async def get_gateway_by_customer_preference(
        cls, 
        customer_country: str, 
        amount_minor: int,
        currency: str,
        preferred_gateways: Optional[list[str]] = None
    ) -> PaymentGateway:
        """Get the best payment gateway based on customer preferences and eligibility."""
        settings = get_settings()
        
        # Use preferred gateways if specified, otherwise use configured ones
        available_gateways = preferred_gateways or settings.enabled_payment_gateways
        
        if not available_gateways:
            # Fallback to mock gateway for development
            logger.warning("No payment gateways configured, using mock gateway")
            return cls.get_gateway("mock")
        
        # Check eligibility for each gateway
        for gateway_name in available_gateways:
            try:
                gateway = cls.get_gateway(gateway_name)
                
                # Check if gateway supports the payment method types
                if gateway_name == "stripe":
                    # Stripe supports most payment methods
                    return gateway
                elif gateway_name == "paypal":
                    # Check PayPal eligibility
                    eligibility = await gateway.get_payment_method_eligibility(
                        "paypal", amount_minor, currency, customer_country
                    )
                    if eligibility["is_eligible"]:
                        return gateway
                elif gateway_name == "mock":
                    # Mock gateway always available
                    return gateway
                    
            except Exception as e:
                logger.warning("Gateway %s not available: %s", gateway_name, str(e))
                continue
        
        # Fallback to first available gateway
        logger.warning("No eligible gateways found, using first available")
        return cls.get_gateway(available_gateways[0])
    
    @classmethod
    def get_gateway_by_payment_method(
        cls, 
        payment_method_type: str,
        customer_country: str
    ) -> Optional[PaymentGateway]:
        """Get the best payment gateway for a specific payment method type."""
        settings = get_settings()
        
        # Map payment method types to preferred gateways
        method_gateway_map = {
            "card": ["stripe", "paypal"],
            "paypal": ["paypal"],
            "apple_pay": ["stripe"],
            "google_pay": ["stripe"],
            "sepa": ["stripe"],
            "ach": ["stripe"],
            "bank_transfer": ["stripe", "paypal"]
        }
        
        preferred_gateways = method_gateway_map.get(payment_method_type, ["stripe", "paypal"])
        
        # Filter by available gateways
        available_gateways = [g for g in preferred_gateways if g in settings.enabled_payment_gateways]
        
        if not available_gateways:
            return None
        
        # Return first available gateway
        return cls.get_gateway(available_gateways[0])
    
    @classmethod
    async def health_check_all(cls) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all available gateways."""
        results = {}
        
        for gateway_name in cls.get_available_gateways():
            try:
                gateway = cls.get_gateway(gateway_name)
                health_status = await gateway.health_check()
                results[gateway_name] = health_status
            except Exception as e:
                logger.error("Health check failed for gateway %s: %s", gateway_name, str(e))
                results[gateway_name] = {
                    "status": "error",
                    "provider": gateway_name,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return results
    
    @classmethod
    def reset_instances(cls) -> None:
        """Reset all gateway instances (useful for testing)."""
        cls._instances.clear()
        logger.info("Reset all payment gateway instances")

    @classmethod
    def get_gateway_by_provider(cls, provider_name: str) -> PaymentGateway:
        """Get gateway instance by provider name."""
        if provider_name not in cls._instances:
            if provider_name not in cls._gateways:
                raise ValueError(f"Unknown payment gateway provider: {provider_name}")
            
            gateway_class = cls._gateways[provider_name]
            cls._instances[provider_name] = gateway_class()
            logger.info("Created payment gateway instance for provider: %s", provider_name)
        
        return cls._instances[provider_name]


# Convenience functions
def get_gateway(name: str) -> PaymentGateway:
    """Get a payment gateway instance by name."""
    return PaymentGatewayFactory.get_gateway(name)


def get_best_gateway(
    customer_country: str,
    amount_minor: int,
    currency: str,
    preferred_gateways: Optional[list[str]] = None
) -> PaymentGateway:
    """Get the best payment gateway for a transaction."""
    return PaymentGatewayFactory.get_gateway_by_customer_preference(
        customer_country, amount_minor, currency, preferred_gateways
    )


def get_gateway_for_payment_method(
    payment_method_type: str,
    customer_country: str
) -> Optional[PaymentGateway]:
    """Get the best payment gateway for a payment method type."""
    return PaymentGatewayFactory.get_gateway_by_payment_method(
        payment_method_type, customer_country
    )


def health_check_all_gateways() -> Dict[str, Dict[str, Any]]:
    """Perform health check on all gateways."""
    return PaymentGatewayFactory.health_check_all()
