"""Tests for subscription service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

from ..subscription_service import SubscriptionService, BillingService
from ..models import Subscription, Invoice, Customer
from ..exceptions import SubscriptionError, BillingError


class TestSubscriptionService:
    """Test subscription service functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_gateway(self):
        """Mock payment gateway."""
        gateway = Mock()
        gateway.create_subscription.return_value = Mock(id="sub_123")
        gateway.cancel_subscription.return_value = None
        gateway.update_subscription.return_value = Mock(id="sub_123")
        return gateway
    
    @pytest.fixture
    def subscription_service(self, mock_db, mock_gateway):
        """Create subscription service instance."""
        return SubscriptionService(mock_db, mock_gateway)
    
    @pytest.fixture
    def customer_id(self):
        """Sample customer ID."""
        return uuid4()
    
    def test_create_subscription_success(self, subscription_service, customer_id, mock_db, mock_gateway):
        """Test successful subscription creation."""
        # Arrange
        plan_id = "basic_monthly"
        plan_name = "Basic Monthly Plan"
        amount = 2999  # $29.99
        currency = "usd"
        interval = "month"
        
        # Act
        result = subscription_service.create_subscription(
            customer_id=customer_id,
            plan_id=plan_id,
            plan_name=plan_name,
            amount=amount,
            currency=currency,
            interval=interval
        )
        
        # Assert
        assert result is not None
        assert result.provider_id == "sub_123"
        assert result.customer_id == customer_id
        assert result.plan_id == plan_id
        assert result.plan_name == plan_name
        assert result.amount == amount
        assert result.currency == currency
        assert result.interval == interval
        assert result.status == "active"
        
        mock_gateway.create_subscription.assert_called_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_subscription_with_trial(self, subscription_service, customer_id, mock_db, mock_gateway):
        """Test subscription creation with trial period."""
        # Arrange
        trial_days = 14
        
        # Act
        result = subscription_service.create_subscription(
            customer_id=customer_id,
            plan_id="basic_monthly",
            plan_name="Basic Monthly Plan",
            amount=2999,
            currency="usd",
            interval="month",
            trial_days=trial_days
        )
        
        # Assert
        assert result.status == "trialing"
        assert result.trial_start is not None
        assert result.trial_end is not None
        assert (result.trial_end - result.trial_start).days == trial_days
    
    def test_create_subscription_gateway_error(self, subscription_service, customer_id, mock_db, mock_gateway):
        """Test subscription creation when gateway fails."""
        # Arrange
        mock_gateway.create_subscription.side_effect = Exception("Gateway error")
        
        # Act & Assert
        with pytest.raises(SubscriptionError, match="Failed to create subscription"):
            subscription_service.create_subscription(
                customer_id=customer_id,
                plan_id="basic_monthly",
                plan_name="Basic Monthly Plan",
                amount=2999,
                currency="usd",
                interval="month"
            )
        
        mock_db.rollback.assert_called_once()
    
    def test_cancel_subscription_success(self, subscription_service, mock_db, mock_gateway):
        """Test successful subscription cancellation."""
        # Arrange
        subscription_id = uuid4()
        subscription = Mock(
            id=subscription_id,
            provider_id="sub_123",
            status="active"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = subscription
        
        # Act
        result = subscription_service.cancel_subscription(subscription_id)
        
        # Assert
        assert result.status == "canceled"
        assert result.canceled_at is not None
        assert result.cancel_at_period_end is True
        
        mock_gateway.cancel_subscription.assert_called_once_with("sub_123", cancel_at_period_end=True)
        mock_db.commit.assert_called_once()
    
    def test_cancel_subscription_immediate(self, subscription_service, mock_db, mock_gateway):
        """Test immediate subscription cancellation."""
        # Arrange
        subscription_id = uuid4()
        subscription = Mock(
            id=subscription_id,
            provider_id="sub_123",
            status="active"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = subscription
        
        # Act
        result = subscription_service.cancel_subscription(
            subscription_id, 
            cancel_at_period_end=False,
            reason="Customer request"
        )
        
        # Assert
        assert result.status == "canceled"
        assert result.cancel_at_period_end is False
        assert result.cancellation_reason == "Customer request"
        
        mock_gateway.cancel_subscription.assert_called_once_with("sub_123", cancel_at_period_end=False)
    
    def test_cancel_subscription_not_found(self, subscription_service, mock_db):
        """Test cancellation of non-existent subscription."""
        # Arrange
        subscription_id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(SubscriptionError, match="Subscription.*not found"):
            subscription_service.cancel_subscription(subscription_id)
    
    def test_update_subscription_success(self, subscription_service, mock_db, mock_gateway):
        """Test successful subscription update."""
        # Arrange
        subscription_id = uuid4()
        subscription = Mock(
            id=subscription_id,
            provider_id="sub_123",
            plan_id="basic_monthly",
            amount=2999,
            metadata={}
        )
        mock_db.query.return_value.filter.return_value.first.return_value = subscription
        
        # Act
        result = subscription_service.update_subscription(
            subscription_id,
            plan_id="premium_monthly",
            amount=4999
        )
        
        # Assert
        assert result.plan_id == "premium_monthly"
        assert result.amount == 4999
        
        mock_gateway.update_subscription.assert_called_once_with(
            "sub_123",
            plan_id="premium_monthly",
            amount=4999,
            metadata=None
        )
    
    def test_process_subscription_renewal_success(self, subscription_service, mock_db):
        """Test successful subscription renewal processing."""
        # Arrange
        subscription_id = uuid4()
        subscription = Mock(
            id=subscription_id,
            customer_id=uuid4(),
            status="active",
            amount=2999,
            currency="usd",
            plan_name="Basic Monthly Plan",
            current_period_start=datetime.utcnow() - timedelta(days=30),
            current_period_end=datetime.utcnow(),
            interval="month",
            interval_count=1
        )
        mock_db.query.return_value.filter.return_value.first.return_value = subscription
        
        # Act
        result = subscription_service.process_subscription_renewal(subscription_id)
        
        # Assert
        assert isinstance(result, Invoice)
        assert result.customer_id == subscription.customer_id
        assert result.amount == subscription.amount
        assert result.currency == subscription.currency
        assert result.status == "draft"
        assert result.subscription_id == subscription_id
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
    
    def test_process_subscription_renewal_trial_expiration(self, subscription_service, mock_db):
        """Test subscription renewal with trial expiration."""
        # Arrange
        subscription_id = uuid4()
        subscription = Mock(
            id=subscription_id,
            customer_id=uuid4(),
            status="trialing",
            amount=2999,
            currency="usd",
            plan_name="Basic Monthly Plan",
            current_period_start=datetime.utcnow() - timedelta(days=30),
            current_period_end=datetime.utcnow(),
            interval="month",
            interval_count=1,
            trial_end=datetime.utcnow() - timedelta(hours=1)
        )
        mock_db.query.return_value.filter.return_value.first.return_value = subscription
        
        # Act
        result = subscription_service.process_subscription_renewal(subscription_id)
        
        # Assert
        assert subscription.status == "active"
        assert subscription.trial_end is None
        assert result is not None
    
    def test_get_subscriptions_by_customer(self, subscription_service, mock_db):
        """Test retrieving subscriptions by customer."""
        # Arrange
        customer_id = uuid4()
        subscriptions = [Mock(), Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.desc.return_value.all.return_value = subscriptions
        
        # Act
        result = subscription_service.get_subscriptions_by_customer(customer_id)
        
        # Assert
        assert result == subscriptions
        mock_db.query.assert_called_once()
    
    def test_get_active_subscriptions(self, subscription_service, mock_db):
        """Test retrieving active subscriptions."""
        # Arrange
        active_subscriptions = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = active_subscriptions
        
        # Act
        result = subscription_service.get_active_subscriptions()
        
        # Assert
        assert result == active_subscriptions
    
    def test_get_subscriptions_due_for_renewal(self, subscription_service, mock_db):
        """Test retrieving subscriptions due for renewal."""
        # Arrange
        due_subscriptions = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = due_subscriptions
        
        # Act
        result = subscription_service.get_subscriptions_due_for_renewal(days_ahead=7)
        
        # Assert
        assert result == due_subscriptions
    
    def test_calculate_interval_delta(self, subscription_service):
        """Test interval delta calculations."""
        # Test daily intervals
        delta = subscription_service._calculate_interval_delta("day", 1)
        assert delta.days == 1
        
        # Test weekly intervals
        delta = subscription_service._calculate_interval_delta("week", 2)
        assert delta.days == 14
        
        # Test monthly intervals
        delta = subscription_service._calculate_interval_delta("month", 1)
        assert delta.days == 30
        
        # Test yearly intervals
        delta = subscription_service._calculate_interval_delta("year", 1)
        assert delta.days == 365
        
        # Test invalid interval
        with pytest.raises(ValueError, match="Unsupported interval"):
            subscription_service._calculate_interval_delta("invalid", 1)


class TestBillingService:
    """Test billing service functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_gateway(self):
        """Mock payment gateway."""
        return Mock()
    
    @pytest.fixture
    def billing_service(self, mock_db, mock_gateway):
        """Create billing service instance."""
        return BillingService(mock_db, mock_gateway)
    
    @pytest.fixture
    def customer_id(self):
        """Sample customer ID."""
        return uuid4()
    
    def test_create_invoice_success(self, billing_service, customer_id, mock_db):
        """Test successful invoice creation."""
        # Arrange
        amount = 2999
        currency = "usd"
        description = "Monthly subscription"
        
        # Act
        result = billing_service.create_invoice(
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            description=description
        )
        
        # Assert
        assert result is not None
        assert result.customer_id == customer_id
        assert result.amount == amount
        assert result.currency == currency
        assert result.description == description
        assert result.status == "draft"
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_finalize_invoice_success(self, billing_service, mock_db):
        """Test successful invoice finalization."""
        # Arrange
        invoice_id = uuid4()
        invoice = Mock(
            id=invoice_id,
            status="draft"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = invoice
        
        # Act
        result = billing_service.finalize_invoice(invoice_id)
        
        # Assert
        assert result.status == "open"
        assert result.finalized_at is not None
        
        mock_db.commit.assert_called_once()
    
    def test_finalize_invoice_wrong_status(self, billing_service, mock_db):
        """Test finalization of invoice with wrong status."""
        # Arrange
        invoice_id = uuid4()
        invoice = Mock(
            id=invoice_id,
            status="open"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = invoice
        
        # Act & Assert
        with pytest.raises(BillingError, match="Invoice.*is not in draft status"):
            billing_service.finalize_invoice(invoice_id)
    
    def test_mark_invoice_paid_success(self, billing_service, mock_db):
        """Test successful invoice payment marking."""
        # Arrange
        invoice_id = uuid4()
        payment_intent_id = uuid4()
        invoice = Mock(
            id=invoice_id,
            status="open"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = invoice
        
        # Act
        result = billing_service.mark_invoice_paid(invoice_id, payment_intent_id)
        
        # Assert
        assert result.status == "paid"
        assert result.paid_at is not None
        assert result.payment_intent_id == payment_intent_id
        
        mock_db.commit.assert_called_once()
    
    def test_get_invoices_by_customer(self, billing_service, mock_db):
        """Test retrieving invoices by customer."""
        # Arrange
        customer_id = uuid4()
        invoices = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.desc.return_value.all.return_value = invoices
        
        # Act
        result = billing_service.get_invoices_by_customer(customer_id)
        
        # Assert
        assert result == invoices
    
    def test_get_overdue_invoices(self, billing_service, mock_db):
        """Test retrieving overdue invoices."""
        # Arrange
        overdue_invoices = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = overdue_invoices
        
        # Act
        result = billing_service.get_overdue_invoices()
        
        # Assert
        assert result == overdue_invoices
