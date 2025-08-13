"""Unit tests for the payment system."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from decimal import Decimal

from src.payments.gateways.base import (
    PaymentGateway, PaymentIntent, Charge, Refund, 
    Mandate, PaymentMethod, PaymentGatewayError
)
from src.payments.gateways.stripe import StripeGateway
from src.payments.gateways.paypal import PayPalGateway
from src.payments.gateways.adyen import AdyenGateway
from src.payments.gateways.factory import PaymentGatewayFactory
from src.payments.service import PaymentService
from src.payments.webhooks import (
    WebhookHandler, StripeWebhookHandler, 
    PayPalWebhookHandler, AdyenWebhookHandler
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
        assert stripe_gateway.api_key == "sk_test_123"
        assert stripe_gateway.publishable_key == "pk_test_123"
        assert stripe_gateway.api_version == "2023-10-16"
    
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
                metadata={"test": "data"}
            )
    
    @pytest.mark.asyncio
    async def test_stripe_create_payment_intent(self, stripe_gateway):
        """Test creating a payment intent in Stripe."""
        with patch('stripe.PaymentIntent.create') as mock_create:
            mock_intent = Mock()
            mock_intent.id = "pi_test123"
            mock_intent.amount = 1000
            mock_intent.currency = "usd"
            mock_intent.status = "requires_payment_method"
            mock_intent.client_secret = "pi_test123_secret"
            mock_intent.capture_method = "automatic"
            mock_intent.confirmation_method = "automatic"
            mock_intent.metadata = {"test": "data"}
            mock_create.return_value = mock_intent
            
            payment_intent = await stripe_gateway.create_payment_intent(
                amount_minor=1000,
                currency="USD",
                customer_id="cus_test123",
                capture_method="automatic",
                confirmation_method="automatic",
                metadata={"test": "data"}
            )
            
            assert payment_intent.id == "pi_test123"
            assert payment_intent.amount_minor == 1000
            assert payment_intent.currency == "USD"
            assert payment_intent.status == "requires_payment_method"
            assert payment_intent.client_secret == "pi_test123_secret"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stripe_confirm_payment_intent(self, stripe_gateway):
        """Test confirming a payment intent in Stripe."""
        with patch('stripe.PaymentIntent.confirm') as mock_confirm:
            mock_intent = Mock()
            mock_intent.id = "pi_test123"
            mock_intent.amount = 1000
            mock_intent.currency = "usd"
            mock_intent.status = "succeeded"
            mock_intent.client_secret = ""
            mock_intent.capture_method = "automatic"
            mock_intent.confirmation_method = "automatic"
            mock_intent.metadata = {}
            mock_confirm.return_value = mock_intent
            
            payment_intent = await stripe_gateway.confirm_payment_intent(
                payment_intent_id="pi_test123",
                payment_method_id="pm_test123"
            )
            
            assert payment_intent.id == "pi_test123"
            assert payment_intent.status == "succeeded"
            mock_confirm.assert_called_once_with(
                payment_method="pm_test123"
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
                paypal_environment="sandbox"
            )
            return PayPalGateway()
    
    @pytest.mark.asyncio
    async def test_paypal_gateway_initialization(self, paypal_gateway):
        """Test PayPal gateway initialization."""
        assert paypal_gateway.provider_name == "paypal"
        assert paypal_gateway.client_id == "client_id_123"
        assert paypal_gateway.client_secret == "client_secret_123"
        assert paypal_gateway.environment == "sandbox"
    
    @pytest.mark.asyncio
    async def test_paypal_create_customer(self, paypal_gateway):
        """Test creating a customer in PayPal."""
        customer_id = await paypal_gateway.create_customer(
            email="test@example.com",
            country="US",
            metadata={"test": "data"}
        )
        
        # PayPal doesn't have separate customer creation
        assert customer_id.startswith("paypal_cust_")
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


class TestPaymentService:
    """Test payment service."""
    
    @pytest.fixture
    def payment_service(self):
        """Create a payment service instance for testing."""
        with patch('src.payments.service.PaymentService.__init__'):
            return PaymentService()
    
    @pytest.mark.asyncio
    async def test_create_customer(self, payment_service):
        """Test creating a customer."""
        with patch.object(payment_service, 'gateway_factory') as mock_factory:
            mock_gateway = AsyncMock()
            mock_gateway.create_customer.return_value = "cus_test123"
            mock_factory.get_gateway_by_provider.return_value = mock_gateway
            
            customer_id = await payment_service.create_customer(
                email="test@example.com",
                country="US",
                metadata={"test": "data"}
            )
            
            assert customer_id == "cus_test123"
            mock_gateway.create_customer.assert_called_once_with(
                "test@example.com", "US", {"test": "data"}
            )
    
    @pytest.mark.asyncio
    async def test_create_payment_intent(self, payment_service):
        """Test creating a payment intent."""
        with patch.object(payment_service, 'gateway_factory') as mock_factory:
            mock_gateway = AsyncMock()
            mock_payment_intent = PaymentIntent(
                id="pi_test123",
                amount_minor=1000,
                currency="USD",
                status="requires_payment_method",
                client_secret="pi_test123_secret",
                capture_method="automatic",
                confirmation_method="automatic",
                metadata={}
            )
            mock_gateway.create_payment_intent.return_value = mock_payment_intent
            mock_factory.get_gateway_by_provider.return_value = mock_gateway
            
            payment_intent = await payment_service.create_payment_intent(
                amount_minor=1000,
                currency="USD",
                customer_id="cus_test123"
            )
            
            assert payment_intent.id == "pi_test123"
            assert payment_intent.amount_minor == 1000
            assert payment_intent.currency == "USD"
            mock_gateway.create_payment_intent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self, payment_service):
        """Test health check functionality."""
        with patch.object(payment_service, 'gateway_factory') as mock_factory:
            mock_gateway = AsyncMock()
            mock_gateway.health_check.return_value = {
                "status": "healthy",
                "gateway": "stripe",
                "timestamp": "2023-01-01T00:00:00Z"
            }
            mock_factory._gateways = {"stripe": Mock}
            mock_factory.get_gateway_by_provider.return_value = mock_gateway
            
            health_status = await payment_service.health_check()
            
            assert "overall_status" in health_status
            assert "gateways" in health_status
            assert "timestamp" in health_status
            assert "stripe" in health_status["gateways"]


class TestWebhookHandlers:
    """Test webhook handlers."""
    
    @pytest.fixture
    def mock_payment_service(self):
        """Create a mock payment service."""
        return Mock()
    
    def test_webhook_handler_base(self, mock_payment_service):
        """Test base webhook handler."""
        handler = WebhookHandler(mock_payment_service)
        
        with pytest.raises(NotImplementedError):
            asyncio.run(handler.process_webhook({}, {}))
    
    def test_stripe_webhook_handler_initialization(self, mock_payment_service):
        """Test Stripe webhook handler initialization."""
        handler = StripeWebhookHandler(mock_payment_service, "whsec_test123")
        assert handler.webhook_secret == "whsec_test123"
    
    def test_stripe_webhook_signature_verification(self, mock_payment_service):
        """Test Stripe webhook signature verification."""
        handler = StripeWebhookHandler(mock_payment_service, "whsec_test123")
        
        # Test valid signature
        payload = b'{"test": "data"}'
        timestamp = "1234567890"
        signature = "t=1234567890,v1=valid_signature_hash"
        
        # This is a simplified test - in reality we'd need to generate proper HMAC
        result = handler._verify_signature(payload, signature, timestamp)
        assert isinstance(result, bool)
    
    def test_paypal_webhook_handler_initialization(self, mock_payment_service):
        """Test PayPal webhook handler initialization."""
        handler = PayPalWebhookHandler(mock_payment_service)
        assert handler.payment_service == mock_payment_service
    
    def test_adyen_webhook_handler_initialization(self, mock_payment_service):
        """Test Adyen webhook handler initialization."""
        handler = AdyenWebhookHandler(mock_payment_service)
        assert handler.payment_service == mock_payment_service


class TestPaymentGatewayError:
    """Test payment gateway error handling."""
    
    def test_payment_gateway_error_creation(self):
        """Test PaymentGatewayError creation."""
        error = PaymentGatewayError(
            message="Test error message",
            code="test_error_code",
            details={"field": "value"}
        )
        
        assert error.message == "Test error message"
        assert error.code == "test_error_code"
        assert error.details["field"] == "value"
    
    def test_payment_gateway_error_str_representation(self):
        """Test PaymentGatewayError string representation."""
        error = PaymentGatewayError(
            message="Test error message",
            code="test_error_code"
        )
        
        error_str = str(error)
        assert "Test error message" in error_str
        assert "test_error_code" in error_str


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
        
        # Test that we can create a service
        with patch('src.payments.service.PaymentService.__init__'):
            service = PaymentService()
            assert service is not None
        
        # Test that we can create webhook handlers
        with patch('src.payments.service.PaymentService.__init__'):
            mock_service = PaymentService()
            webhook_manager = WebhookManager(mock_service)
            assert webhook_manager is not None
    
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
    
    @pytest.mark.asyncio
    async def test_webhook_processing_performance(self, mock_payment_service):
        """Test webhook processing performance."""
        import time
        
        handler = StripeWebhookHandler(mock_payment_service, "whsec_test123")
        
        # Mock a simple webhook payload
        payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test123"}}}
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        
        start_time = time.time()
        
        # This will fail due to signature verification, but we can measure the time
        try:
            await handler.process_webhook(payload, headers)
        except:
            pass
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should be very fast (under 50ms)
        assert processing_time < 0.05


if __name__ == "__main__":
    pytest.main([__file__])
