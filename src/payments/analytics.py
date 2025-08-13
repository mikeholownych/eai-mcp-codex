"""Payment analytics and reporting service."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.orm import Session

from .models import (
    Customer, PaymentIntent, Charge, Refund, Subscription, 
    Invoice, Dispute, AuditLog, PaymentMethod
)
from .exceptions import AnalyticsError

logger = logging.getLogger(__name__)


class PaymentAnalytics:
    """Comprehensive payment analytics and reporting service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_payment_volume(
        self,
        start_date: datetime,
        end_date: datetime,
        currency: Optional[str] = None,
        group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """Get payment volume over time."""
        try:
            query = self.db.query(
                func.date_trunc(group_by, Charge.created_at).label('period'),
                func.sum(Charge.amount_minor).label('total_amount'),
                func.count(Charge.id).label('transaction_count'),
                Charge.currency
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded'
                )
            )
            
            if currency:
                query = query.filter(Charge.currency == currency)
            
            results = query.group_by(
                func.date_trunc(group_by, Charge.created_at),
                Charge.currency
            ).order_by(
                func.date_trunc(group_by, Charge.created_at)
            ).all()
            
            return [
                {
                    'period': result.period,
                    'total_amount': result.total_amount,
                    'transaction_count': result.transaction_count,
                    'currency': result.currency,
                    'total_amount_decimal': Decimal(result.total_amount) / 100
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get payment volume: {e}")
            raise AnalyticsError(f"Failed to get payment volume: {e}")
    
    def get_success_rate(
        self,
        start_date: datetime,
        end_date: datetime,
        gateway: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get payment success rate metrics."""
        try:
            # Get total attempts
            total_query = self.db.query(func.count(PaymentIntent.id))
            if gateway:
                total_query = total_query.join(Charge).filter(
                    Charge.provider_charge_id.like(f"{gateway}_%")
                )
            
            total_attempts = total_query.filter(
                and_(
                    PaymentIntent.created_at >= start_date,
                    PaymentIntent.created_at <= end_date
                )
            ).scalar()
            
            # Get successful payments
            success_query = self.db.query(func.count(Charge.id))
            if gateway:
                success_query = success_query.filter(
                    Charge.provider_charge_id.like(f"{gateway}_%")
                )
            
            successful_payments = success_query.filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded'
                )
            ).scalar()
            
            # Get failed payments
            failed_query = self.db.query(func.count(PaymentIntent.id))
            if gateway:
                failed_query = failed_query.join(Charge).filter(
                    Charge.provider_charge_id.like(f"{gateway}_%")
                )
            
            failed_payments = failed_query.filter(
                and_(
                    PaymentIntent.created_at >= start_date,
                    PaymentIntent.created_at <= end_date,
                    PaymentIntent.status == 'canceled'
                )
            ).scalar()
            
            success_rate = (successful_payments / total_attempts * 100) if total_attempts > 0 else 0
            failure_rate = (failed_payments / total_attempts * 100) if total_attempts > 0 else 0
            
            return {
                'total_attempts': total_attempts,
                'successful_payments': successful_payments,
                'failed_payments': failed_payments,
                'success_rate': round(success_rate, 2),
                'failure_rate': round(failure_rate, 2),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get success rate: {e}")
            raise AnalyticsError(f"Failed to get success rate: {e}")
    
    def get_customer_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get customer-related metrics."""
        try:
            # New customers
            new_customers = self.db.query(func.count(Customer.id)).filter(
                and_(
                    Customer.created_at >= start_date,
                    Customer.created_at <= end_date
                )
            ).scalar()
            
            # Active customers (made payment in period)
            active_customers = self.db.query(
                func.count(func.distinct(Charge.customer_id))
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded'
                )
            ).scalar()
            
            # Total customers
            total_customers = self.db.query(func.count(Customer.id)).scalar()
            
            # Customer retention rate
            previous_period_start = start_date - (end_date - start_date)
            previous_period_customers = self.db.query(
                func.count(func.distinct(Charge.customer_id))
            ).filter(
                and_(
                    Charge.created_at >= previous_period_start,
                    Charge.created_at < start_date,
                    Charge.status == 'succeeded'
                )
            ).scalar()
            
            retention_rate = (
                (active_customers / previous_period_customers * 100) 
                if previous_period_customers > 0 else 0
            )
            
            return {
                'new_customers': new_customers,
                'active_customers': active_customers,
                'total_customers': total_customers,
                'retention_rate': round(retention_rate, 2),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get customer metrics: {e}")
            raise AnalyticsError(f"Failed to get customer metrics: {e}")
    
    def get_revenue_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get revenue-related metrics."""
        try:
            # Gross revenue
            gross_revenue = self.db.query(
                func.sum(Charge.amount_minor)
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded',
                    Charge.currency == currency
                )
            ).scalar() or 0
            
            # Refunds
            refunds = self.db.query(
                func.sum(Refund.amount_minor)
            ).filter(
                and_(
                    Refund.created_at >= start_date,
                    Refund.created_at <= end_date
                )
            ).scalar() or 0
            
            # Net revenue
            net_revenue = gross_revenue - refunds
            
            # Average order value
            avg_order_value = self.db.query(
                func.avg(Charge.amount_minor)
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded',
                    Charge.currency == currency
                )
            ).scalar() or 0
            
            # Revenue by payment method
            revenue_by_method = self.db.query(
                PaymentMethod.brand,
                func.sum(Charge.amount_minor).label('total_amount'),
                func.count(Charge.id).label('transaction_count')
            ).join(
                PaymentMethod, PaymentMethod.customer_id == Charge.customer_id
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded',
                    Charge.currency == currency
                )
            ).group_by(PaymentMethod.brand).all()
            
            return {
                'gross_revenue': gross_revenue,
                'refunds': refunds,
                'net_revenue': net_revenue,
                'gross_revenue_decimal': Decimal(gross_revenue) / 100,
                'refunds_decimal': Decimal(refunds) / 100,
                'net_revenue_decimal': Decimal(net_revenue) / 100,
                'average_order_value': round(avg_order_value, 2),
                'average_order_value_decimal': Decimal(avg_order_value) / 100,
                'revenue_by_payment_method': [
                    {
                        'brand': result.brand or 'unknown',
                        'total_amount': result.total_amount,
                        'total_amount_decimal': Decimal(result.total_amount) / 100,
                        'transaction_count': result.transaction_count
                    }
                    for result in revenue_by_method
                ],
                'currency': currency,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get revenue metrics: {e}")
            raise AnalyticsError(f"Failed to get revenue metrics: {e}")
    
    def get_subscription_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get subscription-related metrics."""
        try:
            # Active subscriptions
            active_subscriptions = self.db.query(
                func.count(Subscription.id)
            ).filter(
                and_(
                    Subscription.status.in_(['active', 'trialing']),
                    Subscription.created_at <= end_date,
                    or_(
                        Subscription.ended_at.is_(None),
                        Subscription.ended_at >= start_date
                    )
                )
            ).scalar()
            
            # New subscriptions
            new_subscriptions = self.db.query(
                func.count(Subscription.id)
            ).filter(
                and_(
                    Subscription.created_at >= start_date,
                    Subscription.created_at <= end_date
                )
            ).scalar()
            
            # Cancelled subscriptions
            cancelled_subscriptions = self.db.query(
                func.count(Subscription.id)
            ).filter(
                and_(
                    Subscription.canceled_at >= start_date,
                    Subscription.canceled_at <= end_date
                )
            ).scalar()
            
            # Churn rate
            churn_rate = (
                (cancelled_subscriptions / active_subscriptions * 100) 
                if active_subscriptions > 0 else 0
            )
            
            # MRR (Monthly Recurring Revenue)
            mrr = self.db.query(
                func.sum(Subscription.amount_minor)
            ).filter(
                and_(
                    Subscription.status.in_(['active', 'trialing']),
                    Subscription.interval == 'month',
                    Subscription.created_at <= end_date,
                    or_(
                        Subscription.ended_at.is_(None),
                        Subscription.ended_at >= start_date
                    )
                )
            ).scalar() or 0
            
            return {
                'active_subscriptions': active_subscriptions,
                'new_subscriptions': new_subscriptions,
                'cancelled_subscriptions': cancelled_subscriptions,
                'churn_rate': round(churn_rate, 2),
                'mrr': mrr,
                'mrr_decimal': Decimal(mrr) / 100,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscription metrics: {e}")
            raise AnalyticsError(f"Failed to get subscription metrics: {e}")
    
    def get_fraud_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get fraud and dispute metrics."""
        try:
            # Disputes
            total_disputes = self.db.query(
                func.count(Dispute.id)
            ).filter(
                and_(
                    Dispute.created_at >= start_date,
                    Dispute.created_at <= end_date
                )
            ).scalar()
            
            # Dispute amount
            dispute_amount = self.db.query(
                func.sum(Dispute.amount_minor)
            ).filter(
                and_(
                    Dispute.created_at >= start_date,
                    Dispute.created_at <= end_date
                )
            ).scalar() or 0
            
            # Disputes by status
            disputes_by_status = self.db.query(
                Dispute.status,
                func.count(Dispute.id).label('count'),
                func.sum(Dispute.amount_minor).label('total_amount')
            ).filter(
                and_(
                    Dispute.created_at >= start_date,
                    Dispute.created_at <= end_date
                )
            ).group_by(Dispute.status).all()
            
            return {
                'total_disputes': total_disputes,
                'dispute_amount': dispute_amount,
                'dispute_amount_decimal': Decimal(dispute_amount) / 100,
                'disputes_by_status': [
                    {
                        'status': result.status,
                        'count': result.count,
                        'total_amount': result.total_amount,
                        'total_amount_decimal': Decimal(result.total_amount) / 100
                    }
                    for result in disputes_by_status
                ],
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get fraud metrics: {e}")
            raise AnalyticsError(f"Failed to get fraud metrics: {e}")
    
    def get_comprehensive_report(
        self,
        start_date: datetime,
        end_date: datetime,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get comprehensive payment analytics report."""
        try:
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'payment_volume': self.get_payment_volume(start_date, end_date, currency),
                'success_rate': self.get_success_rate(start_date, end_date),
                'customer_metrics': self.get_customer_metrics(start_date, end_date),
                'revenue_metrics': self.get_revenue_metrics(start_date, end_date, currency),
                'subscription_metrics': self.get_subscription_metrics(start_date, end_date),
                'fraud_metrics': self.get_fraud_metrics(start_date, end_date),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            raise AnalyticsError(f"Failed to generate comprehensive report: {e}")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time payment metrics."""
        try:
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            
            # Transactions in last hour
            hourly_transactions = self.db.query(
                func.count(Charge.id)
            ).filter(
                and_(
                    Charge.created_at >= last_hour,
                    Charge.status == 'succeeded'
                )
            ).scalar()
            
            # Revenue in last hour
            hourly_revenue = self.db.query(
                func.sum(Charge.amount_minor)
            ).filter(
                and_(
                    Charge.created_at >= last_hour,
                    Charge.status == 'succeeded'
                )
            ).scalar() or 0
            
            # Transactions in last 24 hours
            daily_transactions = self.db.query(
                func.count(Charge.id)
            ).filter(
                and_(
                    Charge.created_at >= last_24h,
                    Charge.status == 'succeeded'
                )
            ).scalar()
            
            # Revenue in last 24 hours
            daily_revenue = self.db.query(
                func.sum(Charge.amount_minor)
            ).filter(
                and_(
                    Charge.created_at >= last_24h,
                    Charge.status == 'succeeded'
                )
            ).scalar() or 0
            
            return {
                'last_hour': {
                    'transactions': hourly_transactions,
                    'revenue': hourly_revenue,
                    'revenue_decimal': Decimal(hourly_revenue) / 100
                },
                'last_24_hours': {
                    'transactions': daily_transactions,
                    'revenue': daily_revenue,
                    'revenue_decimal': Decimal(daily_revenue) / 100
                },
                'timestamp': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            raise AnalyticsError(f"Failed to get real-time metrics: {e}")
