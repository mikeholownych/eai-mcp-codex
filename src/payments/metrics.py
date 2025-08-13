"""Metrics and monitoring for payment operations."""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from .models import PaymentIntent, Charge, Refund, Subscription, Invoice, WebhookEvent

logger = logging.getLogger(__name__)


@dataclass
class PaymentMetrics:
    """Payment performance metrics."""
    total_volume: int
    total_transactions: int
    success_rate: float
    average_amount: float
    failure_rate: float
    chargeback_rate: float
    processing_time_avg: float
    currency_breakdown: Dict[str, int]
    payment_method_breakdown: Dict[str, int]
    gateway_breakdown: Dict[str, int]


@dataclass
class SubscriptionMetrics:
    """Subscription business metrics."""
    total_subscriptions: int
    active_subscriptions: int
    churn_rate: float
    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    average_subscription_value: float
    trial_conversion_rate: float
    plan_distribution: Dict[str, int]


@dataclass
class RevenueMetrics:
    """Revenue and financial metrics."""
    total_revenue: int
    net_revenue: int
    fees_paid: int
    refunds: int
    chargebacks: int
    pending_amount: int
    currency_breakdown: Dict[str, int]
    monthly_growth: float


class PaymentMetricsCollector:
    """Collect and calculate payment metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_payment_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        currency: Optional[str] = None
    ) -> PaymentMetrics:
        """Get comprehensive payment metrics for a date range."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build base query
        base_query = self.db.query(PaymentIntent).filter(
            and_(
                PaymentIntent.created_at >= start_date,
                PaymentIntent.created_at <= end_date
            )
        )
        
        if currency:
            base_query = base_query.filter(PaymentIntent.currency == currency.upper())
        
        # Get total volume and transactions
        total_volume = sum(p.amount for p in base_query.all())
        total_transactions = base_query.count()
        
        if total_transactions == 0:
            return PaymentMetrics(
                total_volume=0,
                total_transactions=0,
                success_rate=0.0,
                average_amount=0.0,
                failure_rate=0.0,
                chargeback_rate=0.0,
                processing_time_avg=0.0,
                currency_breakdown={},
                payment_method_breakdown={},
                gateway_breakdown={}
            )
        
        # Get successful transactions
        successful_query = base_query.filter(PaymentIntent.status == "succeeded")
        successful_transactions = successful_query.count()
        success_rate = (successful_transactions / total_transactions) * 100
        
        # Get failed transactions
        failed_query = base_query.filter(PaymentIntent.status.in_(["failed", "canceled"]))
        failed_transactions = failed_query.count()
        failure_rate = (failed_transactions / total_transactions) * 100
        
        # Calculate average amount
        average_amount = total_volume / total_transactions
        
        # Get chargeback rate
        chargeback_query = self.db.query(Charge).filter(
            and_(
                Charge.created_at >= start_date,
                Charge.created_at <= end_date,
                Charge.status == "chargeback"
            )
        )
        chargeback_count = chargeback_query.count()
        chargeback_rate = (chargeback_count / total_transactions) * 100 if total_transactions > 0 else 0
        
        # Calculate average processing time
        processing_times = []
        for intent in base_query.all():
            if intent.status == "succeeded" and intent.confirmed_at:
                processing_time = (intent.confirmed_at - intent.created_at).total_seconds()
                processing_times.append(processing_time)
        
        processing_time_avg = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Get currency breakdown
        currency_breakdown = {}
        currency_query = self.db.query(
            PaymentIntent.currency,
            func.sum(PaymentIntent.amount)
        ).filter(
            and_(
                PaymentIntent.created_at >= start_date,
                PaymentIntent.created_at <= end_date
            )
        ).group_by(PaymentIntent.currency).all()
        
        for curr, amount in currency_query:
            currency_breakdown[curr] = amount
        
        # Get payment method breakdown
        payment_method_breakdown = {}
        method_query = self.db.query(
            PaymentIntent.payment_method_type,
            func.count(PaymentIntent.id)
        ).filter(
            and_(
                PaymentIntent.created_at >= start_date,
                PaymentIntent.created_at <= end_date
            )
        ).group_by(PaymentIntent.payment_method_type).all()
        
        for method, count in method_query:
            payment_method_breakdown[method or "unknown"] = count
        
        # Get gateway breakdown
        gateway_breakdown = {}
        gateway_query = self.db.query(
            PaymentIntent.gateway,
            func.count(PaymentIntent.id)
        ).filter(
            and_(
                PaymentIntent.created_at >= start_date,
                PaymentIntent.created_at <= end_date
            )
        ).group_by(PaymentIntent.gateway).all()
        
        for gateway, count in gateway_query:
            gateway_breakdown[gateway or "unknown"] = count
        
        return PaymentMetrics(
            total_volume=total_volume,
            total_transactions=total_transactions,
            success_rate=success_rate,
            average_amount=average_amount,
            failure_rate=failure_rate,
            chargeback_rate=chargeback_rate,
            processing_time_avg=processing_time_avg,
            currency_breakdown=currency_breakdown,
            payment_method_breakdown=payment_method_breakdown,
            gateway_breakdown=gateway_breakdown
        )
    
    def get_subscription_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SubscriptionMetrics:
        """Get subscription business metrics."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Total subscriptions
        total_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        ).count()
        
        # Active subscriptions
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.status.in_(["active", "trialing"])
        ).count()
        
        # Calculate churn rate
        canceled_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.canceled_at >= start_date,
                Subscription.canceled_at <= end_date
            )
        ).count()
        
        churn_rate = (canceled_subscriptions / total_subscriptions) * 100 if total_subscriptions > 0 else 0
        
        # Calculate MRR and ARR
        active_sub_query = self.db.query(Subscription).filter(
            Subscription.status.in_(["active", "trialing"])
        )
        
        mrr = sum(sub.amount for sub in active_sub_query.all()) / 100  # Convert from cents
        arr = mrr * 12
        
        # Average subscription value
        if active_subscriptions > 0:
            total_value = sum(sub.amount for sub in active_sub_query.all())
            average_subscription_value = total_value / active_subscriptions / 100
        else:
            average_subscription_value = 0
        
        # Trial conversion rate
        trial_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == "trialing",
                Subscription.trial_end <= end_date
            )
        ).count()
        
        converted_trials = self.db.query(Subscription).filter(
            and_(
                Subscription.status == "active",
                Subscription.trial_end.isnot(None)
            )
        ).count()
        
        trial_conversion_rate = (converted_trials / trial_subscriptions) * 100 if trial_subscriptions > 0 else 0
        
        # Plan distribution
        plan_distribution = {}
        plan_query = self.db.query(
            Subscription.plan_id,
            func.count(Subscription.id)
        ).filter(
            Subscription.status.in_(["active", "trialing"])
        ).group_by(Subscription.plan_id).all()
        
        for plan, count in plan_query:
            plan_distribution[plan] = count
        
        return SubscriptionMetrics(
            total_subscriptions=total_subscriptions,
            active_subscriptions=active_subscriptions,
            churn_rate=churn_rate,
            mrr=mrr,
            arr=arr,
            average_subscription_value=average_subscription_value,
            trial_conversion_rate=trial_conversion_rate,
            plan_distribution=plan_distribution
        )
    
    def get_revenue_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> RevenueMetrics:
        """Get revenue and financial metrics."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Total revenue from successful charges
        total_revenue = self.db.query(func.sum(Charge.amount)).filter(
            and_(
                Charge.created_at >= start_date,
                Charge.created_at <= end_date,
                Charge.status == "succeeded"
            )
        ).scalar() or 0
        
        # Calculate fees (approximate)
        fees_paid = int(total_revenue * 0.029) + (self.db.query(Charge).filter(
            and_(
                Charge.created_at >= start_date,
                Charge.created_at <= end_date,
                Charge.status == "succeeded"
            )
        ).count() * 30)  # 2.9% + 30 cents per transaction
        
        # Net revenue
        net_revenue = total_revenue - fees_paid
        
        # Refunds
        refunds = self.db.query(func.sum(Refund.amount)).filter(
            and_(
                Refund.created_at >= start_date,
                Refund.created_at <= end_date
            )
        ).scalar() or 0
        
        # Chargebacks
        chargebacks = self.db.query(func.sum(Charge.amount)).filter(
            and_(
                Charge.created_at >= start_date,
                Charge.created_at <= end_date,
                Charge.status == "chargeback"
            )
        ).scalar() or 0
        
        # Pending amount
        pending_amount = self.db.query(func.sum(PaymentIntent.amount)).filter(
            and_(
                PaymentIntent.created_at >= start_date,
                PaymentIntent.created_at <= end_date,
                PaymentIntent.status == "processing"
            )
        ).scalar() or 0
        
        # Currency breakdown
        currency_breakdown = {}
        currency_query = self.db.query(
            Charge.currency,
            func.sum(Charge.amount)
        ).filter(
            and_(
                Charge.created_at >= start_date,
                Charge.created_at <= end_date,
                Charge.status == "succeeded"
            )
        ).group_by(Charge.currency).all()
        
        for curr, amount in currency_query:
            currency_breakdown[curr] = amount
        
        # Calculate monthly growth
        previous_month_start = start_date - timedelta(days=30)
        previous_month_revenue = self.db.query(func.sum(Charge.amount)).filter(
            and_(
                Charge.created_at >= previous_month_start,
                Charge.created_at < start_date,
                Charge.status == "succeeded"
            )
        ).scalar() or 0
        
        monthly_growth = ((total_revenue - previous_month_revenue) / previous_month_revenue) * 100 if previous_month_revenue > 0 else 0
        
        return RevenueMetrics(
            total_revenue=total_revenue,
            net_revenue=net_revenue,
            fees_paid=fees_paid,
            refunds=refunds,
            chargebacks=chargebacks,
            pending_amount=pending_amount,
            currency_breakdown=currency_breakdown,
            monthly_growth=monthly_growth
        )
    
    def get_daily_metrics(
        self,
        days: int = 30,
        currency: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get daily metrics for the specified number of days."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        daily_metrics = []
        
        for i in range(days):
            current_date = end_date - timedelta(days=i)
            day_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Build query for this day
            day_query = self.db.query(PaymentIntent).filter(
                and_(
                    PaymentIntent.created_at >= day_start,
                    PaymentIntent.created_at < day_end
                )
            )
            
            if currency:
                day_query = day_query.filter(PaymentIntent.currency == currency.upper())
            
            day_transactions = day_query.all()
            
            total_volume = sum(t.amount for t in day_transactions)
            total_count = len(day_transactions)
            successful_count = len([t for t in day_transactions if t.status == "succeeded"])
            
            success_rate = (successful_count / total_count) * 100 if total_count > 0 else 0
            
            daily_metrics.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "total_volume": total_volume,
                "total_transactions": total_count,
                "successful_transactions": successful_count,
                "success_rate": success_rate
            })
        
        return list(reversed(daily_metrics))
    
    def get_gateway_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics by payment gateway."""
        gateways = self.db.query(PaymentIntent.gateway).distinct().all()
        gateway_metrics = {}
        
        for (gateway,) in gateways:
            if not gateway:
                continue
            
            # Get metrics for this gateway
            gateway_query = self.db.query(PaymentIntent).filter(
                PaymentIntent.gateway == gateway
            )
            
            total_transactions = gateway_query.count()
            successful_transactions = gateway_query.filter(
                PaymentIntent.status == "succeeded"
            ).count()
            
            success_rate = (successful_transactions / total_transactions) * 100 if total_transactions > 0 else 0
            
            # Calculate average processing time
            processing_times = []
            for intent in gateway_query.filter(PaymentIntent.status == "succeeded").all():
                if intent.confirmed_at:
                    processing_time = (intent.confirmed_at - intent.created_at).total_seconds()
                    processing_times.append(processing_time)
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            gateway_metrics[gateway] = {
                "total_transactions": total_transactions,
                "successful_transactions": successful_transactions,
                "success_rate": success_rate,
                "average_processing_time": avg_processing_time
            }
        
        return gateway_metrics


class MetricsExporter:
    """Export metrics to various monitoring systems."""
    
    def __init__(self):
        self.metrics_buffer = []
    
    def export_to_prometheus(self, metrics: PaymentMetrics) -> str:
        """Export metrics in Prometheus format."""
        prometheus_metrics = []
        
        # Payment metrics
        prometheus_metrics.append(f"payment_total_volume {metrics.total_volume}")
        prometheus_metrics.append(f"payment_total_transactions {metrics.total_transactions}")
        prometheus_metrics.append(f"payment_success_rate {metrics.success_rate}")
        prometheus_metrics.append(f"payment_failure_rate {metrics.failure_rate}")
        prometheus_metrics.append(f"payment_chargeback_rate {metrics.chargeback_rate}")
        prometheus_metrics.append(f"payment_processing_time_avg {metrics.processing_time_avg}")
        
        # Currency breakdown
        for currency, amount in metrics.currency_breakdown.items():
            prometheus_metrics.append(f'payment_volume_by_currency{{currency="{currency}"}} {amount}')
        
        # Payment method breakdown
        for method, count in metrics.payment_method_breakdown.items():
            prometheus_metrics.append(f'payment_transactions_by_method{{method="{method}"}} {count}')
        
        # Gateway breakdown
        for gateway, count in metrics.gateway_breakdown.items():
            prometheus_metrics.append(f'payment_transactions_by_gateway{{gateway="{gateway}"}} {count}')
        
        return "\n".join(prometheus_metrics)
    
    def export_to_json(self, metrics: PaymentMetrics) -> Dict[str, Any]:
        """Export metrics as JSON."""
        return asdict(metrics)
    
    def export_to_csv(self, daily_metrics: List[Dict[str, Any]]) -> str:
        """Export daily metrics as CSV."""
        if not daily_metrics:
            return ""
        
        headers = daily_metrics[0].keys()
        csv_lines = [",".join(headers)]
        
        for metric in daily_metrics:
            row = [str(metric.get(header, "")) for header in headers]
            csv_lines.append(",".join(row))
        
        return "\n".join(csv_lines)
