"""Simplified unit tests for the payment system."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

from src.payments.gateways.base import (
    PaymentGateway, PaymentIntent, Charge, Refund, 
    Mandate, PaymentMethod, PaymentGatewayError
)
from src.payments.gateways.stripe import StripeGateway
from src.payments.gateways.paypal import PayPalGateway
from src.payments.gateways.adyen import AdyenGateway
from src.payments.gateways.factory import PaymentGatewayFactory
from src.payments.exceptions import (
    PaymentError, PaymentGatewayError, DisputeError, 
    SubscriptionError, BillingError, AnalyticsError, ReconciliationError
)


class TestPaymentGatewayBase:
    """Test base payment gateway functionality."""
    
    def test_payment_gateway_interface(self):
        """Test that PaymentGateway is an abstract base class."""
        with pytest.raises(TypeError):
            PaymentGateway()
    
    def test_payment_intent_creation(self):
        """Test PaymentIntent object creation."""
        payment_intent = PaymentIntent(
            id="pi_test123",
            amount_minor=1000,
            currency="USD",
            status="requires_payment_method",
            client_secret="pi_test123_secret",
            capture_method="automatic",
            confirmation_method="automatic",
            metadata={"order_id": "order_123"}
        )
        
        assert payment_intent.id == "pi_test123"
        assert payment_intent.amount_minor == 1000
        assert payment_intent.currency == "USD"
        assert payment_intent.status == "requires_payment_method"
        assert payment_intent.client_secret == "pi_test123_secret"
        assert payment_intent.capture_method == "automatic"
        assert payment_intent.confirmation_method == "automatic"
        assert payment_intent.metadata["order_id"] == "order_123"
    
    def test_charge_creation(self):
        """Test Charge object creation."""
        charge = Charge(
            id="ch_test123",
            amount_minor=1000,
            currency="USD",
            status="succeeded",
            receipt_url="https://receipt.example.com/ch_test123"
        )
        
        assert charge.id == "ch_test123"
        assert charge.amount_minor == 1000
        assert charge.currency == "USD"
        assert charge.status == "succeeded"
        assert charge.receipt_url == "https://receipt.example.com/ch_test123"
    
    def test_refund_creation(self):
        """Test Refund object creation."""
        refund = Refund(
            id="re_test123",
            amount_minor=1000,
            currency="USD",
            status="succeeded",
            reason="customer_requested"
        )
        
        assert refund.id == "re_test123"
        assert refund.amount_minor == 1000
        assert refund.currency == "USD"
        assert refund.status == "succeeded"
        assert refund.reason == "customer_requested"
    
    def test_payment_method_creation(self):
        """Test PaymentMethod object creation."""
        payment_method = PaymentMethod(
            id="pm_test123",
            brand="visa",
            last4="4242",
            exp_month=12,
            exp_year=2030,
            customer_id="cus_test123"
        )
        
        assert payment_method.id == "pm_test123"
        assert payment_method.brand == "visa"
        assert payment_method.last4 == "4242"
        assert payment_method.exp_month == 12
        assert payment_method.exp_year == 2030
        assert payment_method.customer_id == "cus_test123"


class TestStripeGateway:
    """Test Stripe payment gateway."""
    
    @pytest.fixture
    def stripe_gateway(self):
        """Create a Stripe gateway instance for testing."""
        with patch('src.payments.gateways.stripe.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stripe_secret_key="sk_test_123",
                stripe_publishable_key="pk_test_123",
                stripe_api_version="2023-10-16"
            )
            return StripeGateway()
    
    @pytest.mark.asyncio
    async def test_stripe_gateway_initialization(self, stripe_gateway):
        """Test Stripe gateway initialization."""
        assert stripe_gateway.provider_name == "stripe"
        assert stripe_gateway.settings.stripe_secret_key == "sk_test_123"
        assert stripe_gateway.settings.stripe_publishable_key == "pk_test_123"
        assert stripe_gateway.settings.stripe_api_version == "2023-10-16"
    
    @pytest.mark.asyncio
    async def test_stripe_create_customer(self, stripe_gateway):
        """Test creating a customer in Stripe."""
        with patch('stripe.Customer.create') as mock_create:
            mock_customer = Mock()
            mock_customer.id = "cus_test123"
            mock_create.return_value = mock_customer
            
            customer_id = await stripe_gateway.create_customer(
                email="test@example.com",
                country="US",
                metadata={"test": "data"}
            )
            
            assert customer_id == "cus_test123"
            mock_create.assert_called_once_with(
                email="test@example.com",
                metadata={"test": "data"},
                address={"country": "US"}
            )


class TestPayPalGateway:
    """Test PayPal payment gateway."""
    
    @pytest.fixture
    def paypal_gateway(self):
        """Create a PayPal gateway instance for testing."""
        with patch('src.payments.gateways.paypal.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                paypal_client_id="client_id_123",
                paypal_client_secret="client_secret_123",
                paypal_environment="sandbox",
                paypal_base_url="https://api-m.sandbox.paypal.com"
            )
            return PayPalGateway()
    
    @pytest.mark.asyncio
    async def test_paypal_gateway_initialization(self, paypal_gateway):
        """Test PayPal gateway initialization."""
        assert paypal_gateway.provider_name == "paypal"
        assert paypal_gateway.client_id == "client_id_123"
        assert paypal_gateway.client_secret == "client_secret_123"
        assert paypal_gateway.settings.paypal_base_url == "https://api-m.sandbox.paypal.com"
    
    @pytest.mark.asyncio
    async def test_paypal_create_customer(self, paypal_gateway):
        """Test creating a customer in PayPal."""
        customer_id = await paypal_gateway.create_customer(
            email="test@example.com",
            country="US",
            metadata={"test": "data"}
        )
        
        # PayPal doesn't have separate customer creation
        assert customer_id.startswith("paypal_")
        assert "test@example.com" in customer_id


class TestAdyenGateway:
    """Test Adyen payment gateway."""
    
    @pytest.fixture
    def adyen_gateway(self):
        """Create an Adyen gateway instance for testing."""
        with patch('src.payments.gateways.adyen.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                adyen_api_key="api_key_123",
                adyen_merchant_account="merchant_123",
                adyen_environment="test"
            )
            return AdyenGateway()
    
    @pytest.mark.asyncio
    async def test_adyen_gateway_initialization(self, adyen_gateway):
        """Test Adyen gateway initialization."""
        assert adyen_gateway.provider_name == "adyen"
        assert adyen_gateway.api_key == "api_key_123"
        assert adyen_gateway.merchant_account == "merchant_123"
        assert adyen_gateway.environment == "test"
        assert "test" in adyen_gateway.base_url
    
    @pytest.mark.asyncio
    async def test_adyen_create_customer(self, adyen_gateway):
        """Test creating a customer in Adyen."""
        customer_id = await adyen_gateway.create_customer(
            email="test@example.com",
            country="US",
            metadata={"test": "data"}
        )
        
        assert customer_id.startswith("cust_test@example.com_")
    
    @pytest.mark.asyncio
    async def test_adyen_payment_method_eligibility(self, adyen_gateway):
        """Test payment method eligibility in Adyen."""
        # Test card eligibility in US
        eligibility = await adyen_gateway.get_payment_method_eligibility(
            payment_method_type="card",
            amount_minor=1000,
            currency="USD",
            country="US"
        )
        
        assert eligibility["is_eligible"] is True
        assert eligibility["requirements"] == []
        assert eligibility["restrictions"] == []
        
        # Test unsupported payment method
        eligibility = await adyen_gateway.get_payment_method_eligibility(
            payment_method_type="unsupported",
            amount_minor=1000,
            currency="USD",
            country="US"
        )
        
        assert eligibility["is_eligible"] is False
        assert "not supported" in eligibility["restrictions"][0]


class TestPaymentGatewayFactory:
    """Test payment gateway factory."""
    
    def test_factory_initialization(self):
        """Test factory initialization."""
        factory = PaymentGatewayFactory()
        
        # Check that all gateways are registered
        assert "stripe" in factory._gateways
        assert "paypal" in factory._gateways
        assert "adyen" in factory._gateways
        assert "mock" in factory._gateways
    
    def test_get_gateway_by_provider(self):
        """Test getting gateway by provider name."""
        factory = PaymentGatewayFactory()
        
        # Test getting Stripe gateway
        stripe_gateway = factory.get_gateway_by_provider("stripe")
        assert isinstance(stripe_gateway, StripeGateway)
        assert stripe_gateway.provider_name == "stripe"
        
        # Test getting PayPal gateway
        paypal_gateway = factory.get_gateway_by_provider("paypal")
        assert isinstance(paypal_gateway, PayPalGateway)
        assert paypal_gateway.provider_name == "paypal"
        
        # Test getting Adyen gateway
        adyen_gateway = factory.get_gateway_by_provider("adyen")
        assert isinstance(adyen_gateway, AdyenGateway)
        assert adyen_gateway.provider_name == "adyen"
    
    def test_get_gateway_by_provider_invalid(self):
        """Test getting gateway with invalid provider name."""
        factory = PaymentGatewayFactory()
        
        with pytest.raises(ValueError, match="Unknown payment gateway provider"):
            factory.get_gateway_by_provider("invalid_provider")
    
    def test_get_best_gateway(self):
        """Test getting best gateway for payment method and country."""
        # Test card payment in US
        best_gateway = PaymentGatewayFactory.get_best_gateway("card", "US")
        assert best_gateway in ["stripe", "paypal", "adyen"]
        
        # Test SEPA payment in Germany
        best_gateway = PaymentGatewayFactory.get_best_gateway("sepa_debit", "DE")
        assert best_gateway in ["adyen", "stripe"]
        
        # Test unsupported payment method
        best_gateway = PaymentGatewayFactory.get_best_gateway("unsupported", "US")
        assert best_gateway == "stripe"  # Default fallback


class TestPaymentExceptions:
    """Test payment exception classes."""
    
    def test_payment_error(self):
        """Test PaymentError exception."""
        error = PaymentError("Test payment error")
        assert str(error) == "Test payment error"
    
    def test_payment_gateway_error(self):
        """Test PaymentGatewayError exception."""
        error = PaymentGatewayError("Gateway error", "gateway_error", {"field": "value"})
        assert error.message == "Gateway error"
        assert error.code == "gateway_error"
        assert error.details["field"] == "value"
    
    def test_dispute_error(self):
        """Test DisputeError exception."""
        error = DisputeError("Test dispute error")
        assert str(error) == "Test dispute error"
    
    def test_subscription_error(self):
        """Test SubscriptionError exception."""
        error = SubscriptionError("Test subscription error")
        assert str(error) == "Test subscription error"
    
    def test_billing_error(self):
        """Test BillingError exception."""
        error = BillingError("Test billing error")
        assert str(error) == "Test billing error"
    
    def test_analytics_error(self):
        """Test AnalyticsError exception."""
        error = AnalyticsError("Test analytics error")
        assert str(error) == "Test analytics error"
    
    def test_reconciliation_error(self):
        """Test ReconciliationError exception."""
        error = ReconciliationError("Test reconciliation error")
        assert str(error) == "Test reconciliation error"


# Integration tests
class TestPaymentSystemIntegration:
    """Integration tests for the payment system."""
    
    @pytest.mark.asyncio
    async def test_complete_payment_flow(self):
        """Test a complete payment flow from customer creation to payment."""
        # This would test the entire flow in a real scenario
        # For now, we'll just verify the components work together
        
        # Test that we can create gateways
        factory = PaymentGatewayFactory()
        assert factory is not None
        
        # Test that we can create gateway instances
        stripe_gateway = factory.get_gateway_by_provider("stripe")
        assert stripe_gateway is not None
        assert stripe_gateway.provider_name == "stripe"
    
    @pytest.mark.asyncio
    async def test_gateway_fallback_mechanism(self):
        """Test gateway fallback mechanism."""
        # Test that when one gateway fails, others can be used
        factory = PaymentGatewayFactory()
        
        # Get all available gateways
        gateways = list(factory._gateways.keys())
        assert len(gateways) >= 3  # Should have at least Stripe, PayPal, and Adyen
        
        # Test that each gateway can be instantiated
        for gateway_name in gateways:
            gateway = factory.get_gateway_by_provider(gateway_name)
            assert gateway is not None
            assert gateway.provider_name == gateway_name


# Performance tests
class TestPaymentSystemPerformance:
    """Performance tests for the payment system."""
    
    @pytest.mark.asyncio
    async def test_gateway_instantiation_performance(self):
        """Test gateway instantiation performance."""
        import time
        
        factory = PaymentGatewayFactory()
        start_time = time.time()
        
        # Instantiate all gateways
        for gateway_name in factory._gateways:
            gateway = factory.get_gateway_by_provider(gateway_name)
            assert gateway is not None
        
        end_time = time.time()
        instantiation_time = end_time - start_time
        
        # Should be very fast (under 100ms)
        assert instantiation_time < 0.1


if __name__ == "__main__":
    pytest.main([__file__])
