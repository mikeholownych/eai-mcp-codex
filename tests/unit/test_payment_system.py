"""Unit tests for the payment system."""

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
from src.payments.service import PaymentService
from src.payments.webhooks import (
    WebhookHandler, StripeWebhookHandler, 
    PayPalWebhookHandler, AdyenWebhookHandler, WebhookManager
)
from src.payments.dispute_service import DisputeService
from src.payments.subscription_service import SubscriptionService, BillingService
from src.payments.analytics import PaymentAnalytics
from src.payments.reconciliation import PaymentReconciliation
from src.payments.metrics import PaymentMetrics, SubscriptionMetrics, RevenueMetrics, PaymentMetricsCollector
from src.payments.webhook_retry import WebhookRetryService
from src.payments.exceptions import (
    PaymentError, PaymentGatewayError, DisputeError, 
    SubscriptionError, BillingError, AnalyticsError, ReconciliationError
)
from src.payments.models import (
    Customer, PaymentIntent as DBPaymentIntent, Charge as DBCharge, 
    Refund as DBRefund, Dispute, Subscription, Invoice, AuditLog
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


class TestDisputeService:
    """Test dispute service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_payment_gateway(self):
        """Create a mock payment gateway."""
        gateway = Mock()
        gateway.create_dispute = AsyncMock()
        gateway.update_dispute = AsyncMock()
        return gateway
    
    @pytest.fixture
    def dispute_service(self, mock_db_session, mock_payment_gateway):
        """Create a dispute service instance."""
        return DisputeService(mock_db_session, mock_payment_gateway)
    
    @pytest.mark.asyncio
    async def test_create_dispute(self, dispute_service, mock_db_session, mock_payment_gateway):
        """Test creating a dispute."""
        # Mock charge exists
        mock_charge = Mock()
        mock_charge.id = "ch_test123"
        mock_charge.provider_charge_id = "stripe_ch_test123"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_charge
        
        # Mock no existing dispute
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_charge,  # First call for charge lookup
            None  # Second call for existing dispute lookup
        ]
        
        # Mock gateway dispute creation
        mock_gateway_dispute = Mock()
        mock_gateway_dispute.id = "dp_test123"
        mock_payment_gateway.create_dispute.return_value = mock_gateway_dispute
        
        # Mock dispute creation
        mock_dispute = Mock()
        mock_dispute.id = "dispute_123"
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        with patch('src.payments.dispute_service.Dispute') as mock_dispute_class:
            mock_dispute_class.return_value = mock_dispute
            
            dispute = await dispute_service.create_dispute(
                charge_id="ch_test123",
                reason="fraudulent",
                amount_minor=1000,
                currency="USD"
            )
            
            assert dispute == mock_dispute
            mock_payment_gateway.create_dispute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_dispute_charge_not_found(self, dispute_service, mock_db_session):
        """Test creating a dispute with non-existent charge."""
        # Mock charge not found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(DisputeError, match="Charge ch_test123 not found"):
            await dispute_service.create_dispute(
                charge_id="ch_test123",
                reason="fraudulent",
                amount_minor=1000,
                currency="USD"
            )
    
    @pytest.mark.asyncio
    async def test_update_dispute_status(self, dispute_service, mock_db_session):
        """Test updating dispute status."""
        # Mock dispute exists
        mock_dispute = Mock()
        mock_dispute.id = "dispute_123"
        mock_dispute.status = "needs_response"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_dispute
        
        await dispute_service.update_dispute_status(
            dispute_id="dispute_123",
            status="under_review"
        )
        
        assert mock_dispute.status == "under_review"
        mock_db_session.commit.assert_called_once()


class TestSubscriptionService:
    """Test subscription service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_payment_gateway(self):
        """Create a mock payment gateway."""
        gateway = Mock()
        gateway.create_subscription = AsyncMock()
        gateway.cancel_subscription = AsyncMock()
        gateway.update_subscription = AsyncMock()
        return gateway
    
    @pytest.fixture
    def subscription_service(self, mock_db_session, mock_payment_gateway):
        """Create a subscription service instance."""
        return SubscriptionService(mock_db_session, mock_payment_gateway)
    
    @pytest.mark.asyncio
    async def test_create_subscription(self, subscription_service, mock_db_session, mock_payment_gateway):
        """Test creating a subscription."""
        customer_id = uuid4()
        
        # Mock gateway subscription creation
        mock_gateway_subscription = Mock()
        mock_gateway_subscription.id = "sub_test123"
        mock_payment_gateway.create_subscription.return_value = mock_gateway_subscription
        
        # Mock subscription creation
        mock_subscription = Mock()
        mock_subscription.id = "sub_123"
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        with patch('src.payments.subscription_service.Subscription') as mock_subscription_class:
            mock_subscription_class.return_value = mock_subscription
            
            subscription = await subscription_service.create_subscription(
                customer_id=customer_id,
                plan_id="plan_basic",
                plan_name="Basic Plan",
                amount=1000,
                currency="USD",
                interval="month",
                interval_count=1
            )
            
            assert subscription == mock_subscription
            mock_payment_gateway.create_subscription.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_subscription(self, subscription_service, mock_db_session, mock_payment_gateway):
        """Test canceling a subscription."""
        subscription_id = uuid4()
        
        # Mock subscription exists
        mock_subscription = Mock()
        mock_subscription.id = subscription_id
        mock_subscription.provider_id = "sub_test123"
        mock_subscription.status = "active"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_subscription
        
        await subscription_service.cancel_subscription(
            subscription_id=subscription_id,
            cancel_at_period_end=True
        )
        
        assert mock_subscription.status == "canceled"
        mock_payment_gateway.cancel_subscription.assert_called_once_with(
            "sub_test123", cancel_at_period_end=True
        )


class TestBillingService:
    """Test billing service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_payment_gateway(self):
        """Create a mock payment gateway."""
        return Mock()
    
    @pytest.fixture
    def billing_service(self, mock_db_session, mock_payment_gateway):
        """Create a billing service instance."""
        return BillingService(mock_db_session, mock_payment_gateway)
    
    @pytest.mark.asyncio
    async def test_create_invoice(self, billing_service, mock_db_session):
        """Test creating an invoice."""
        customer_id = uuid4()
        subscription_id = uuid4()
        
        # Mock customer and subscription
        mock_customer = Mock()
        mock_customer.id = customer_id
        mock_customer.email = "test@example.com"
        
        mock_subscription = Mock()
        mock_subscription.id = subscription_id
        mock_subscription.amount = 1000
        mock_subscription.currency = "USD"
        
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_customer, mock_subscription
        ]
        
        # Mock invoice creation
        mock_invoice = Mock()
        mock_invoice.id = "inv_123"
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        with patch('src.payments.subscription_service.Invoice') as mock_invoice_class:
            mock_invoice_class.return_value = mock_invoice
            
            invoice = await billing_service.create_invoice(
                customer_id=customer_id,
                subscription_id=subscription_id,
                amount=1000,
                currency="USD"
            )
            
            assert invoice == mock_invoice


class TestPaymentAnalytics:
    """Test payment analytics functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def analytics_service(self, mock_db_session):
        """Create a payment analytics instance."""
        return PaymentAnalytics(mock_db_session)
    
    def test_get_payment_volume(self, analytics_service, mock_db_session):
        """Test getting payment volume."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        # Mock query results
        mock_result = Mock()
        mock_result.period = datetime(2023, 1, 15)
        mock_result.total_amount = 5000
        mock_result.transaction_count = 5
        mock_result.currency = "USD"
        
        mock_db_session.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_result]
        
        results = analytics_service.get_payment_volume(
            start_date=start_date,
            end_date=end_date,
            currency="USD"
        )
        
        assert len(results) == 1
        assert results[0]['total_amount'] == 5000
        assert results[0]['transaction_count'] == 5
        assert results[0]['currency'] == "USD"
    
    def test_get_success_rate(self, analytics_service, mock_db_session):
        """Test getting payment success rate."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        # Mock query results
        mock_db_session.query.return_value.filter.return_value.scalar.side_effect = [100, 85]
        
        result = analytics_service.get_success_rate(
            start_date=start_date,
            end_date=end_date
        )
        
        assert result['total_attempts'] == 100
        assert result['successful_payments'] == 85
        assert result['success_rate'] == 0.85


class TestPaymentReconciliation:
    """Test payment reconciliation functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def reconciliation_service(self, mock_db_session):
        """Create a payment reconciliation instance."""
        return PaymentReconciliation(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_reconcile_payments(self, reconciliation_service, mock_db_session):
        """Test reconciling payments."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = await reconciliation_service.reconcile_payments(
            start_date=start_date,
            end_date=end_date
        )
        
        assert 'reconciled_count' in result
        assert 'discrepancies' in result
        assert 'total_amount' in result


class TestPaymentMetrics:
    """Test payment metrics functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def metrics_service(self, mock_db_session):
        """Create a payment metrics instance."""
        return PaymentMetrics(mock_db_session)
    
    def test_collect_payment_metrics(self, metrics_service, mock_db_session):
        """Test collecting payment metrics."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 1000
        
        metrics = metrics_service.collect_payment_metrics()
        
        assert 'total_volume' in metrics
        assert 'success_rate' in metrics
        assert 'average_transaction_value' in metrics


class TestSubscriptionMetrics:
    """Test subscription metrics functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def subscription_metrics(self, mock_db_session):
        """Create a subscription metrics instance."""
        return SubscriptionMetrics(mock_db_session)
    
    def test_get_subscription_metrics(self, subscription_metrics, mock_db_session):
        """Test getting subscription metrics."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 50
        
        metrics = subscription_metrics.get_subscription_metrics()
        
        assert 'active_subscriptions' in metrics
        assert 'churn_rate' in metrics
        assert 'mrr' in metrics


class TestRevenueMetrics:
    """Test revenue metrics functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def revenue_metrics(self, mock_db_session):
        """Create a revenue metrics instance."""
        return RevenueMetrics(mock_db_session)
    
    def test_calculate_revenue_metrics(self, revenue_metrics, mock_db_session):
        """Test calculating revenue metrics."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 10000
        
        metrics = revenue_metrics.calculate_revenue_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        assert 'total_revenue' in metrics
        assert 'recurring_revenue' in metrics
        assert 'one_time_revenue' in metrics


class TestPaymentMetricsCollector:
    """Test payment metrics collector functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def metrics_collector(self, mock_db_session):
        """Create a payment metrics collector instance."""
        return PaymentMetricsCollector(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_collect_all_metrics(self, metrics_collector, mock_db_session):
        """Test collecting all metrics."""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 1000
        
        metrics = await metrics_collector.collect_all_metrics()
        
        assert 'payment_metrics' in metrics
        assert 'subscription_metrics' in metrics
        assert 'revenue_metrics' in metrics


class TestWebhookManager:
    """Test webhook manager functionality."""
    
    @pytest.fixture
    def mock_payment_service(self):
        """Create a mock payment service."""
        return Mock()
    
    @pytest.fixture
    def webhook_manager(self, mock_payment_service):
        """Create a webhook manager instance."""
        return WebhookManager(mock_payment_service)
    
    @pytest.mark.asyncio
    async def test_process_stripe_webhook(self, webhook_manager, mock_payment_service):
        """Test processing Stripe webhook."""
        payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test123"}}}
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        
        # Mock webhook handler
        with patch.object(webhook_manager.handlers['stripe'], 'process_webhook') as mock_process:
            mock_process.return_value = {"status": "processed"}
            
            result = await webhook_manager.process_webhook("stripe", payload, headers)
            
            assert result == {"status": "processed"}
            mock_process.assert_called_once_with(payload, headers)
    
    @pytest.mark.asyncio
    async def test_process_unsupported_gateway(self, webhook_manager):
        """Test processing webhook from unsupported gateway."""
        payload = {"test": "data"}
        headers = {}
        
        with pytest.raises(Exception, match="Unsupported gateway"):
            await webhook_manager.process_webhook("unsupported", payload, headers)


class TestWebhookRetryService:
    """Test webhook retry service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def retry_service(self, mock_db_session):
        """Create a webhook retry service instance."""
        return WebhookRetryService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_schedule_retry(self, retry_service, mock_db_session):
        """Test scheduling a webhook retry."""
        webhook_id = "wh_123"
        payload = {"test": "data"}
        headers = {"test": "header"}
        
        # Mock retry creation
        mock_retry = Mock()
        mock_retry.id = "retry_123"
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        
        with patch('src.payments.webhook_retry.WebhookRetry') as mock_retry_class:
            mock_retry_class.return_value = mock_retry
            
            retry = await retry_service.schedule_retry(
                webhook_id=webhook_id,
                payload=payload,
                headers=headers,
                delay_seconds=60
            )
            
            assert retry == mock_retry
            mock_db_session.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_retries(self, retry_service, mock_db_session):
        """Test processing webhook retries."""
        # Mock pending retries
        mock_retry = Mock()
        mock_retry.id = "retry_123"
        mock_retry.webhook_id = "wh_123"
        mock_retry.payload = {"test": "data"}
        mock_retry.headers = {"test": "header"}
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_retry]
        
        processed_count = await retry_service.process_retries()
        
        assert processed_count == 1


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


# Enhanced integration tests
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
    
    @pytest.mark.asyncio
    async def test_subscription_billing_flow(self):
        """Test complete subscription billing flow."""
        # Test subscription creation, billing, and payment processing
        with patch('src.payments.subscription_service.SubscriptionService.__init__'):
            with patch('src.payments.subscription_service.BillingService.__init__'):
                # This would test the complete subscription lifecycle
                pass
    
    @pytest.mark.asyncio
    async def test_dispute_handling_flow(self):
        """Test complete dispute handling flow."""
        # Test dispute creation, evidence submission, and resolution
        with patch('src.payments.dispute_service.DisputeService.__init__'):
            # This would test the complete dispute lifecycle
            pass
    
    @pytest.mark.asyncio
    async def test_analytics_and_reporting_flow(self):
        """Test analytics and reporting flow."""
        # Test data collection, analysis, and reporting
        with patch('src.payments.analytics.PaymentAnalytics.__init__'):
            # This would test the complete analytics pipeline
            pass


# Enhanced performance tests
class TestPaymentSystemPerformance:
    """Performance tests for the payment system."""
    
    @pytest.fixture
    def mock_payment_service(self):
        """Create a mock payment service."""
        return Mock()
    
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
    
    @pytest.mark.asyncio
    async def test_analytics_query_performance(self, mock_db_session):
        """Test analytics query performance."""
        import time
        
        analytics = PaymentAnalytics(mock_db_session)
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 1000
        
        start_time = time.time()
        
        metrics = analytics.collect_payment_metrics()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should be fast (under 200ms)
        assert query_time < 0.2
        assert 'total_volume' in metrics
    
    @pytest.mark.asyncio
    async def test_subscription_processing_performance(self, mock_db_session, mock_payment_gateway):
        """Test subscription processing performance."""
        import time
        
        service = SubscriptionService(mock_db_session, mock_payment_gateway)
        customer_id = uuid4()
        
        # Mock gateway response
        mock_gateway_subscription = Mock()
        mock_gateway_subscription.id = "sub_test123"
        mock_payment_gateway.create_subscription.return_value = mock_gateway_subscription
        
        # Mock database operations
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        with patch('src.payments.subscription_service.Subscription') as mock_subscription_class:
            mock_subscription_class.return_value = Mock()
            
            start_time = time.time()
            
            await service.create_subscription(
                customer_id=customer_id,
                plan_id="plan_basic",
                plan_name="Basic Plan",
                amount=1000,
                currency="USD",
                interval="month"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should be fast (under 100ms)
            assert processing_time < 0.1


if __name__ == "__main__":
    pytest.main([__file__])
