"""Tests for the payment service."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..app import app
from ..models import Base, Customer, PaymentIntent, Charge, Refund
from ..gateways.stripe import StripeGateway
from ..gateways.mock import MockGateway
from ..config import get_settings


# Test database setup
@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def client(test_db):
    """Create test client with test database."""
    app.dependency_overrides = {}
    return TestClient(app)


@pytest.fixture
def mock_stripe_gateway():
    """Mock Stripe gateway."""
    with patch('src.payments.app.StripeGateway') as mock:
        gateway = Mock(spec=StripeGateway)
        gateway.create_customer = AsyncMock(return_value="cus_test123")
        gateway.create_payment_intent = AsyncMock(return_value=Mock(
            id="pi_test123",
            amount_minor=1000,
            currency="USD",
            status="requires_payment_method",
            capture_method="automatic",
            confirmation_method="automatic",
            three_ds_status=None,
            metadata={}
        ))
        gateway.confirm_payment_intent = AsyncMock(return_value=Mock(
            status="succeeded",
            three_ds_status=None
        ))
        gateway.capture_payment_intent = AsyncMock(return_value=Mock(
            id="ch_test123",
            status="succeeded",
            receipt_url="https://receipt.test/123"
        ))
        gateway.create_refund = AsyncMock(return_value=Mock(
            id="re_test123",
            amount_minor=1000,
            status="succeeded",
            reason="requested_by_customer"
        ))
        gateway.health_check = AsyncMock(return_value={
            "status": "healthy",
            "provider": "stripe",
            "timestamp": datetime.utcnow().isoformat()
        })
        mock.return_value = gateway
        yield gateway


@pytest.fixture
def mock_mock_gateway():
    """Mock Mock gateway."""
    with patch('src.payments.app.MockGateway') as mock:
        gateway = Mock(spec=MockGateway)
        gateway.create_customer = AsyncMock(return_value="mock_cus_123")
        gateway.create_payment_intent = AsyncMock(return_value=Mock(
            id="mock_pi_123",
            amount_minor=1000,
            currency="USD",
            status="requires_payment_method",
            capture_method="automatic",
            confirmation_method="automatic",
            three_ds_status=None,
            metadata={}
        ))
        gateway.health_check = AsyncMock(return_value={
            "status": "healthy",
            "provider": "mock",
            "timestamp": datetime.utcnow().isoformat()
        })
        mock.return_value = gateway
        yield gateway


class TestCustomerEndpoints:
    """Test customer-related endpoints."""
    
    def test_create_customer_success(self, client, mock_stripe_gateway, test_db):
        """Test successful customer creation."""
        response = client.post(
            "/customers",
            json={
                "email": "test@example.com",
                "country": "US",
                "metadata": {"source": "test"}
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["country"] == "US"
        assert "id" in data
        assert "external_id" in data
    
    def test_create_customer_invalid_country(self, client):
        """Test customer creation with invalid country."""
        response = client.post(
            "/customers",
            json={
                "email": "test@example.com",
                "country": "INVALID",
                "metadata": {"source": "test"}
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 422
    
    def test_create_customer_missing_email(self, client):
        """Test customer creation with missing email."""
        response = client.post(
            "/customers",
            json={
                "country": "US",
                "metadata": {"source": "test"}
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 422
    
    def test_get_customer_success(self, client, test_db):
        """Test successful customer retrieval."""
        # Create test customer
        customer = Customer(
            external_id="cus_test123",
            email="test@example.com",
            country="US"
        )
        test_db.add(customer)
        test_db.commit()
        
        response = client.get(f"/customers/{customer.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["country"] == "US"
    
    def test_get_customer_not_found(self, client):
        """Test customer retrieval for non-existent customer."""
        response = client.get("/customers/non-existent-id")
        assert response.status_code == 404


class TestPaymentIntentEndpoints:
    """Test payment intent-related endpoints."""
    
    def test_create_payment_intent_success(self, client, mock_stripe_gateway, test_db):
        """Test successful payment intent creation."""
        # Create test customer first
        customer = Customer(
            external_id="cus_test123",
            email="test@example.com",
            country="US"
        )
        test_db.add(customer)
        test_db.commit()
        
        response = client.post(
            "/payment-intents",
            json={
                "amount_minor": 1000,
                "currency": "USD",
                "customer_id": str(customer.id),
                "capture_method": "automatic",
                "confirmation_method": "automatic",
                "metadata": {"order_id": "123"}
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount_minor"] == 1000
        assert data["currency"] == "USD"
        assert data["status"] == "requires_payment_method"
        assert "id" in data
    
    def test_create_payment_intent_invalid_amount(self, client):
        """Test payment intent creation with invalid amount."""
        response = client.post(
            "/payment-intents",
            json={
                "amount_minor": -100,
                "currency": "USD",
                "customer_id": "test-customer-id",
                "capture_method": "automatic",
                "confirmation_method": "automatic"
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 422
    
    def test_create_payment_intent_invalid_currency(self, client):
        """Test payment intent creation with invalid currency."""
        response = client.post(
            "/payment-intents",
            json={
                "amount_minor": 1000,
                "currency": "INVALID",
                "customer_id": "test-customer-id",
                "capture_method": "automatic",
                "confirmation_method": "automatic"
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 422
    
    def test_create_payment_intent_customer_not_found(self, client, mock_stripe_gateway):
        """Test payment intent creation with non-existent customer."""
        response = client.post(
            "/payment-intents",
            json={
                "amount_minor": 1000,
                "currency": "USD",
                "customer_id": "non-existent-customer",
                "capture_method": "automatic",
                "confirmation_method": "automatic"
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 404
    
    def test_confirm_payment_intent_success(self, client, mock_stripe_gateway, test_db):
        """Test successful payment intent confirmation."""
        # Create test payment intent
        payment_intent = PaymentIntent(
            provider_id="pi_test123",
            customer_id="test-customer-id",
            amount_minor=1000,
            currency="USD",
            status="requires_confirmation",
            capture_method="automatic",
            confirmation_method="automatic",
            idempotency_key="test-key-123"
        )
        test_db.add(payment_intent)
        test_db.commit()
        
        response = client.post(
            f"/payment-intents/{payment_intent.id}/confirm",
            json={
                "payment_method_id": "pm_test123"
            },
            headers={"Idempotency-Key": "test-key-456"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "succeeded"
    
    def test_confirm_payment_intent_not_found(self, client):
        """Test payment intent confirmation for non-existent intent."""
        response = client.post(
            "/payment-intents/non-existent-id/confirm",
            json={
                "payment_method_id": "pm_test123"
            },
            headers={"Idempotency-Key": "test-key-456"}
        )
        
        assert response.status_code == 404
    
    def test_get_payment_intent_success(self, client, test_db):
        """Test successful payment intent retrieval."""
        # Create test payment intent
        payment_intent = PaymentIntent(
            provider_id="pi_test123",
            customer_id="test-customer-id",
            amount_minor=1000,
            currency="USD",
            status="requires_payment_method",
            capture_method="automatic",
            confirmation_method="automatic",
            idempotency_key="test-key-123"
        )
        test_db.add(payment_intent)
        test_db.commit()
        
        response = client.get(f"/payment-intents/{payment_intent.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["amount_minor"] == 1000
        assert data["currency"] == "USD"
    
    def test_get_payment_intent_not_found(self, client):
        """Test payment intent retrieval for non-existent intent."""
        response = client.get("/payment-intents/non-existent-id")
        assert response.status_code == 404


class TestChargeEndpoints:
    """Test charge-related endpoints."""
    
    def test_capture_payment_intent_success(self, client, mock_stripe_gateway, test_db):
        """Test successful payment intent capture."""
        # Create test payment intent with manual capture
        payment_intent = PaymentIntent(
            provider_id="pi_test123",
            customer_id="test-customer-id",
            amount_minor=1000,
            currency="USD",
            status="requires_capture",
            capture_method="manual",
            confirmation_method="automatic",
            idempotency_key="test-key-123"
        )
        test_db.add(payment_intent)
        test_db.commit()
        
        response = client.post(
            f"/payment-intents/{payment_intent.id}/capture",
            json={"amount_minor": 1000},
            headers={"Idempotency-Key": "test-key-456"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "charge_id" in data
    
    def test_capture_payment_intent_automatic_capture(self, client, test_db):
        """Test capture of payment intent with automatic capture."""
        # Create test payment intent with automatic capture
        payment_intent = PaymentIntent(
            provider_id="pi_test123",
            customer_id="test-customer-id",
            amount_minor=1000,
            currency="USD",
            status="requires_capture",
            capture_method="automatic",
            confirmation_method="automatic",
            idempotency_key="test-key-123"
        )
        test_db.add(payment_intent)
        test_db.commit()
        
        response = client.post(
            f"/payment-intents/{payment_intent.id}/capture",
            json={"amount_minor": 1000},
            headers={"Idempotency-Key": "test-key-456"}
        )
        
        assert response.status_code == 400
        assert "not configured for manual capture" in response.json()["detail"]
    
    def test_capture_payment_intent_wrong_status(self, client, test_db):
        """Test capture of payment intent in wrong status."""
        # Create test payment intent in wrong status
        payment_intent = PaymentIntent(
            provider_id="pi_test123",
            customer_id="test-customer-id",
            amount_minor=1000,
            currency="USD",
            status="requires_payment_method",
            capture_method="manual",
            confirmation_method="automatic",
            idempotency_key="test-key-123"
        )
        test_db.add(payment_intent)
        test_db.commit()
        
        response = client.post(
            f"/payment-intents/{payment_intent.id}/capture",
            json={"amount_minor": 1000},
            headers={"Idempotency-Key": "test-key-456"}
        )
        
        assert response.status_code == 400
        assert "not in capture state" in response.json()["detail"]


class TestRefundEndpoints:
    """Test refund-related endpoints."""
    
    def test_create_refund_success(self, client, mock_stripe_gateway, test_db):
        """Test successful refund creation."""
        # Create test charge
        charge = Charge(
            payment_intent_id="test-intent-id",
            provider_charge_id="ch_test123",
            status="succeeded",
            receipt_url="https://receipt.test/123"
        )
        test_db.add(charge)
        test_db.commit()
        
        response = client.post(
            f"/charges/{charge.id}/refunds",
            json={
                "amount_minor": 1000,
                "reason": "requested_by_customer"
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "refund_id" in data
    
    def test_create_refund_charge_not_found(self, client):
        """Test refund creation for non-existent charge."""
        response = client.post(
            "/charges/non-existent-id/refunds",
            json={
                "amount_minor": 1000,
                "reason": "requested_by_customer"
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 404


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client, mock_stripe_gateway):
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["provider"] == "stripe"
        assert "timestamp" in data


class TestWebhookEndpoints:
    """Test webhook endpoints."""
    
    def test_stripe_webhook_missing_signature(self, client):
        """Test Stripe webhook without signature."""
        response = client.post("/webhooks/stripe", json={"test": "data"})
        assert response.status_code == 400
        assert "Missing Stripe signature" in response.json()["detail"]
    
    def test_stripe_webhook_success(self, client, test_db):
        """Test successful Stripe webhook processing."""
        # Mock the webhook handler
        with patch('src.payments.app.StripeWebhookHandler') as mock_handler:
            mock_instance = Mock()
            mock_instance.process_webhook = AsyncMock()
            mock_handler.return_value = mock_instance
            
            response = client.post(
                "/webhooks/stripe",
                json={"test": "data"},
                headers={"stripe-signature": "test-signature"}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "received"


class TestIdempotency:
    """Test idempotency functionality."""
    
    def test_create_payment_intent_idempotency(self, client, mock_stripe_gateway, test_db):
        """Test payment intent creation idempotency."""
        # Create test customer first
        customer = Customer(
            external_id="cus_test123",
            email="test@example.com",
            country="US"
        )
        test_db.add(customer)
        test_db.commit()
        
        idempotency_key = "test-idempotency-key-123"
        
        # First request
        response1 = client.post(
            "/payment-intents",
            json={
                "amount_minor": 1000,
                "currency": "USD",
                "customer_id": str(customer.id),
                "capture_method": "automatic",
                "confirmation_method": "automatic"
            },
            headers={"Idempotency-Key": idempotency_key}
        )
        
        assert response1.status_code == 201
        first_intent_id = response1.json()["id"]
        
        # Second request with same idempotency key
        response2 = client.post(
            "/payment-intents",
            json={
                "amount_minor": 1000,
                "currency": "USD",
                "customer_id": str(customer.id),
                "capture_method": "automatic",
                "confirmation_method": "automatic"
            },
            headers={"Idempotency-Key": idempotency_key}
        )
        
        assert response2.status_code == 201
        second_intent_id = response2.json()["id"]
        
        # Should return the same payment intent
        assert first_intent_id == second_intent_id


class TestErrorHandling:
    """Test error handling."""
    
    def test_payment_gateway_error_handling(self, client, mock_stripe_gateway):
        """Test payment gateway error handling."""
        # Mock gateway to raise an error
        mock_stripe_gateway.create_customer.side_effect = Exception("Payment gateway error")
        
        response = client.post(
            "/customers",
            json={
                "email": "test@example.com",
                "country": "US"
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["message"]
    
    def test_validation_error_handling(self, client):
        """Test validation error handling."""
        response = client.post(
            "/customers",
            json={
                "email": "invalid-email",
                "country": "INVALID"
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
