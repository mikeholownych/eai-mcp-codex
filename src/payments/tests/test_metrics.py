"""Tests for payment metrics and monitoring."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

from ..metrics import (
    PaymentMetricsCollector, 
    MetricsExporter,
    PaymentMetrics,
    SubscriptionMetrics,
    RevenueMetrics
)
from ..models import PaymentIntent, Charge, Refund, Subscription, Invoice


class TestPaymentMetricsCollector:
    """Test payment metrics collection functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def metrics_collector(self, mock_db):
        """Create metrics collector instance."""
        return PaymentMetricsCollector(mock_db)
    
    @pytest.fixture
    def sample_payment_intents(self):
        """Sample payment intents for testing."""
        return [
            Mock(
                id=uuid4(),
                amount=1000,
                currency="USD",
                status="succeeded",
                payment_method_type="card",
                gateway="stripe",
                created_at=datetime.utcnow() - timedelta(hours=1),
                confirmed_at=datetime.utcnow() - timedelta(minutes=30)
            ),
            Mock(
                id=uuid4(),
                amount=2500,
                currency="USD",
                status="succeeded",
                payment_method_type="card",
                gateway="stripe",
                created_at=datetime.utcnow() - timedelta(hours=2),
                confirmed_at=datetime.utcnow() - timedelta(hours=1, minutes=30)
            ),
            Mock(
                id=uuid4(),
                amount=1500,
                currency="EUR",
                status="failed",
                payment_method_type="card",
                gateway="stripe",
                created_at=datetime.utcnow() - timedelta(hours=3),
                confirmed_at=None
            )
        ]
    
    @pytest.fixture
    def sample_charges(self):
        """Sample charges for testing."""
        return [
            Mock(
                id=uuid4(),
                amount=1000,
                currency="USD",
                status="succeeded",
                created_at=datetime.utcnow() - timedelta(hours=1)
            ),
            Mock(
                id=uuid4(),
                amount=2500,
                currency="USD",
                status="succeeded",
                created_at=datetime.utcnow() - timedelta(hours=2)
            ),
            Mock(
                id=uuid4(),
                amount=1500,
                currency="EUR",
                status="chargeback",
                created_at=datetime.utcnow() - timedelta(hours=3)
            )
        ]
    
    @pytest.fixture
    def sample_subscriptions(self):
        """Sample subscriptions for testing."""
        return [
            Mock(
                id=uuid4(),
                status="active",
                amount=2999,
                created_at=datetime.utcnow() - timedelta(days=30)
            ),
            Mock(
                id=uuid4(),
                status="trialing",
                amount=4999,
                created_at=datetime.utcnow() - timedelta(days=15)
            ),
            Mock(
                id=uuid4(),
                status="canceled",
                amount=1999,
                canceled_at=datetime.utcnow() - timedelta(days=5),
                created_at=datetime.utcnow() - timedelta(days=60)
            )
        ]
    
    def test_get_payment_metrics_success(self, metrics_collector, mock_db, sample_payment_intents):
        """Test successful payment metrics collection."""
        # Arrange
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow()
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = sample_payment_intents
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        
        # Mock successful transactions query
        successful_query = Mock()
        successful_query.count.return_value = 2
        mock_db.query.return_value.filter.return_value.filter.return_value = successful_query
        
        # Mock failed transactions query
        failed_query = Mock()
        failed_query.count.return_value = 1
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value = failed_query
        
        # Mock chargeback query
        chargeback_query = Mock()
        chargeback_query.count.return_value = 1
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = chargeback_query
        
        # Mock currency breakdown query
        currency_query = Mock()
        currency_query.group_by.return_value.all.return_value = [("USD", 3500), ("EUR", 1500)]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value = currency_query
        
        # Mock payment method breakdown query
        method_query = Mock()
        method_query.group_by.return_value.all.return_value = [("card", 3)]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value = method_query
        
        # Mock gateway breakdown query
        gateway_query = Mock()
        gateway_query.group_by.return_value.all.return_value = [("stripe", 3)]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value = gateway_query
        
        # Act
        result = metrics_collector.get_payment_metrics(start_date, end_date)
        
        # Assert
        assert isinstance(result, PaymentMetrics)
        assert result.total_volume == 5000  # 1000 + 2500 + 1500
        assert result.total_transactions == 3
        assert result.success_rate == pytest.approx(66.67, rel=0.01)
        assert result.failure_rate == pytest.approx(33.33, rel=0.01)
        assert result.chargeback_rate == pytest.approx(33.33, rel=0.01)
        assert result.currency_breakdown == {"USD": 3500, "EUR": 1500}
        assert result.payment_method_breakdown == {"card": 3}
        assert result.gateway_breakdown == {"stripe": 3}
    
    def test_get_payment_metrics_no_transactions(self, metrics_collector, mock_db):
        """Test payment metrics when no transactions exist."""
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        # Act
        result = metrics_collector.get_payment_metrics()
        
        # Assert
        assert result.total_volume == 0
        assert result.total_transactions == 0
        assert result.success_rate == 0.0
        assert result.failure_rate == 0.0
        assert result.chargeback_rate == 0.0
    
    def test_get_subscription_metrics(self, metrics_collector, mock_db, sample_subscriptions):
        """Test subscription metrics collection."""
        # Arrange
        start_date = datetime.utcnow() - timedelta(days=60)
        end_date = datetime.utcnow()
        
        # Mock total subscriptions query
        total_query = Mock()
        total_query.count.return_value = 3
        mock_db.query.return_value.filter.return_value = total_query
        
        # Mock active subscriptions query
        active_query = Mock()
        active_query.all.return_value = sample_subscriptions[:2]  # active + trialing
        mock_db.query.return_value.filter.return_value.filter.return_value = active_query
        
        # Mock canceled subscriptions query
        canceled_query = Mock()
        canceled_query.count.return_value = 1
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value = canceled_query
        
        # Mock trial subscriptions query
        trial_query = Mock()
        trial_query.count.return_value = 1
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = trial_query
        
        # Mock converted trials query
        converted_query = Mock()
        converted_query.count.return_value = 0
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = converted_query
        
        # Mock plan distribution query
        plan_query = Mock()
        plan_query.group_by.return_value.all.return_value = [("basic", 1), ("premium", 1)]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value = plan_query
        
        # Act
        result = metrics_collector.get_subscription_metrics(start_date, end_date)
        
        # Assert
        assert isinstance(result, SubscriptionMetrics)
        assert result.total_subscriptions == 3
        assert result.active_subscriptions == 2
        assert result.churn_rate == pytest.approx(33.33, rel=0.01)
        assert result.mrr == pytest.approx(79.98, rel=0.01)  # (2999 + 4999) / 100
        assert result.arr == pytest.approx(959.76, rel=0.01)  # MRR * 12
        assert result.trial_conversion_rate == 0.0
        assert result.plan_distribution == {"basic": 1, "premium": 1}
    
    def test_get_revenue_metrics(self, metrics_collector, mock_db, sample_charges):
        """Test revenue metrics collection."""
        # Arrange
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        # Mock successful charges query
        successful_charges_query = Mock()
        successful_charges_query.scalar.return_value = 3500  # 1000 + 2500
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value = successful_charges_query
        
        # Mock charges count for fees calculation
        charges_count_query = Mock()
        charges_count_query.count.return_value = 2
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = charges_count_query
        
        # Mock refunds query
        refunds_query = Mock()
        refunds_query.scalar.return_value = 500
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = refunds_query
        
        # Mock chargebacks query
        chargebacks_query = Mock()
        chargebacks_query.scalar.return_value = 1500
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = chargebacks_query
        
        # Mock pending amount query
        pending_query = Mock()
        pending_query.scalar.return_value = 1000
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = pending_query
        
        # Mock currency breakdown query
        currency_query = Mock()
        currency_query.group_by.return_value.all.return_value = [("USD", 3500)]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value = currency_query
        
        # Mock previous month revenue query
        prev_month_query = Mock()
        prev_month_query.scalar.return_value = 3000
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = prev_month_query
        
        # Act
        result = metrics_collector.get_revenue_metrics(start_date, end_date)
        
        # Assert
        assert isinstance(result, RevenueMetrics)
        assert result.total_revenue == 3500
        assert result.fees_paid == 131  # (3500 * 0.029) + (2 * 30)
        assert result.net_revenue == 3369
        assert result.refunds == 500
        assert result.chargebacks == 1500
        assert result.pending_amount == 1000
        assert result.currency_breakdown == {"USD": 3500}
        assert result.monthly_growth == pytest.approx(16.67, rel=0.01)  # (3500 - 3000) / 3000 * 100
    
    def test_get_daily_metrics(self, metrics_collector, mock_db):
        """Test daily metrics collection."""
        # Arrange
        days = 3
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        
        # Act
        result = metrics_collector.get_daily_metrics(days=days)
        
        # Assert
        assert len(result) == days
        assert all("date" in metric for metric in result)
        assert all("total_volume" in metric for metric in result)
        assert all("total_transactions" in metric for metric in result)
        assert all("successful_transactions" in metric for metric in result)
        assert all("success_rate" in metric for metric in result)
    
    def test_get_gateway_performance(self, metrics_collector, mock_db):
        """Test gateway performance metrics."""
        # Arrange
        # Mock distinct gateways query
        gateways_query = Mock()
        gateways_query.distinct.return_value.all.return_value = [("stripe",), ("paypal",)]
        mock_db.query.return_value.filter.return_value.distinct.return_value = gateways_query
        
        # Mock gateway-specific queries
        gateway_query = Mock()
        gateway_query.count.return_value = 10
        gateway_query.filter.return_value.count.return_value = 8
        
        # Mock successful transactions for processing time calculation
        successful_query = Mock()
        successful_query.filter.return_value.all.return_value = [
            Mock(
                created_at=datetime.utcnow() - timedelta(minutes=5),
                confirmed_at=datetime.utcnow()
            ),
            Mock(
                created_at=datetime.utcnow() - timedelta(minutes=3),
                confirmed_at=datetime.utcnow()
            )
        ]
        gateway_query.filter.return_value.filter.return_value = successful_query
        
        mock_db.query.return_value.filter.return_value.filter.return_value = gateway_query
        
        # Act
        result = metrics_collector.get_gateway_performance()
        
        # Assert
        assert "stripe" in result
        assert "paypal" in result
        assert result["stripe"]["total_transactions"] == 10
        assert result["stripe"]["successful_transactions"] == 8
        assert result["stripe"]["success_rate"] == 80.0


class TestMetricsExporter:
    """Test metrics export functionality."""
    
    @pytest.fixture
    def metrics_exporter(self):
        """Create metrics exporter instance."""
        return MetricsExporter()
    
    @pytest.fixture
    def sample_payment_metrics(self):
        """Sample payment metrics for testing."""
        return PaymentMetrics(
            total_volume=5000,
            total_transactions=10,
            success_rate=80.0,
            average_amount=500.0,
            failure_rate=20.0,
            chargeback_rate=5.0,
            processing_time_avg=2.5,
            currency_breakdown={"USD": 5000},
            payment_method_breakdown={"card": 8, "bank_transfer": 2},
            gateway_breakdown={"stripe": 10}
        )
    
    @pytest.fixture
    def sample_daily_metrics(self):
        """Sample daily metrics for testing."""
        return [
            {
                "date": "2024-01-01",
                "total_volume": 1000,
                "total_transactions": 2,
                "successful_transactions": 2,
                "success_rate": 100.0
            },
            {
                "date": "2024-01-02",
                "total_volume": 2000,
                "total_transactions": 4,
                "successful_transactions": 3,
                "success_rate": 75.0
            }
        ]
    
    def test_export_to_prometheus(self, metrics_exporter, sample_payment_metrics):
        """Test Prometheus format export."""
        # Act
        result = metrics_exporter.export_to_prometheus(sample_payment_metrics)
        
        # Assert
        assert "payment_total_volume 5000" in result
        assert "payment_total_transactions 10" in result
        assert "payment_success_rate 80.0" in result
        assert "payment_failure_rate 20.0" in result
        assert "payment_chargeback_rate 5.0" in result
        assert "payment_processing_time_avg 2.5" in result
        assert 'payment_volume_by_currency{currency="USD"} 5000' in result
        assert 'payment_transactions_by_method{method="card"} 8' in result
        assert 'payment_transactions_by_gateway{gateway="stripe"} 10' in result
    
    def test_export_to_json(self, metrics_exporter, sample_payment_metrics):
        """Test JSON format export."""
        # Act
        result = metrics_exporter.export_to_json(sample_payment_metrics)
        
        # Assert
        assert isinstance(result, dict)
        assert result["total_volume"] == 5000
        assert result["total_transactions"] == 10
        assert result["success_rate"] == 80.0
        assert result["currency_breakdown"] == {"USD": 5000}
        assert result["payment_method_breakdown"] == {"card": 8, "bank_transfer": 2}
        assert result["gateway_breakdown"] == {"stripe": 10}
    
    def test_export_to_csv(self, metrics_exporter, sample_daily_metrics):
        """Test CSV format export."""
        # Act
        result = metrics_exporter.export_to_csv(sample_daily_metrics)
        
        # Assert
        assert "date,total_volume,total_transactions,successful_transactions,success_rate" in result
        assert "2024-01-01,1000,2,2,100.0" in result
        assert "2024-01-02,2000,4,3,75.0" in result
    
    def test_export_to_csv_empty_data(self, metrics_exporter):
        """Test CSV export with empty data."""
        # Act
        result = metrics_exporter.export_to_csv([])
        
        # Assert
        assert result == ""
    
    def test_export_to_csv_single_row(self, metrics_exporter):
        """Test CSV export with single row of data."""
        # Arrange
        single_metric = [{"date": "2024-01-01", "volume": 1000}]
        
        # Act
        result = metrics_exporter.export_to_csv(single_metric)
        
        # Assert
        assert "date,volume" in result
        assert "2024-01-01,1000" in result
