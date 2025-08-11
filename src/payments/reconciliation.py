"""Payment reconciliation service for financial auditing and discrepancy detection."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
from uuid import uuid4

from .models import (
    Charge, Refund, PaymentIntent, Customer, PaymentMethod,
    WebhookEvent, AuditLog, Invoice, Subscription
)
from .exceptions import ReconciliationError
from .gateways.base import PaymentGateway

logger = logging.getLogger(__name__)


class PaymentReconciliation:
    """Service for reconciling payments and detecting discrepancies."""
    
    def __init__(self, db: Session, payment_gateway: PaymentGateway):
        self.db = db
        self.payment_gateway = payment_gateway
    
    def reconcile_payments(
        self,
        start_date: datetime,
        end_date: datetime,
        gateway: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reconcile payments between local system and payment gateway."""
        try:
            # Get local payment records
            local_payments = self._get_local_payments(start_date, end_date, gateway)
            
            # Get gateway payment records
            gateway_payments = await self._get_gateway_payments(start_date, end_date, gateway)
            
            # Perform reconciliation
            reconciliation_result = self._perform_reconciliation(
                local_payments, gateway_payments
            )
            
            # Log reconciliation
            await self._log_reconciliation(reconciliation_result)
            
            return reconciliation_result
            
        except Exception as e:
            logger.error(f"Failed to reconcile payments: {e}")
            raise ReconciliationError(f"Failed to reconcile payments: {e}")
    
    def _get_local_payments(
        self,
        start_date: datetime,
        end_date: datetime,
        gateway: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get payment records from local database."""
        query = self.db.query(
            Charge.id,
            Charge.provider_charge_id,
            Charge.amount_minor,
            Charge.status,
            Charge.created_at,
            Charge.customer_id,
            PaymentIntent.currency,
            PaymentIntent.idempotency_key
        ).join(
            PaymentIntent, Charge.payment_intent_id == PaymentIntent.id
        ).filter(
            and_(
                Charge.created_at >= start_date,
                Charge.created_at <= end_date
            )
        )
        
        if gateway:
            query = query.filter(Charge.provider_charge_id.like(f"{gateway}_%"))
        
        results = query.all()
        
        return [
            {
                'id': str(result.id),
                'provider_charge_id': result.provider_charge_id,
                'amount_minor': result.amount_minor,
                'status': result.status,
                'created_at': result.created_at,
                'customer_id': str(result.customer_id),
                'currency': result.currency,
                'idempotency_key': result.idempotency_key
            }
            for result in results
        ]
    
    async def _get_gateway_payments(
        self,
        start_date: datetime,
        end_date: datetime,
        gateway: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get payment records from payment gateway."""
        try:
            # This would typically call the gateway's API to get payment records
            # For now, we'll return an empty list as a placeholder
            # In a real implementation, this would fetch from Stripe, PayPal, etc.
            return []
            
        except Exception as e:
            logger.error(f"Failed to get gateway payments: {e}")
            return []
    
    def _perform_reconciliation(
        self,
        local_payments: List[Dict[str, Any]],
        gateway_payments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform reconciliation between local and gateway payments."""
        # Create lookup dictionaries
        local_lookup = {
            payment['provider_charge_id']: payment 
            for payment in local_payments
        }
        gateway_lookup = {
            payment['provider_charge_id']: payment 
            for payment in gateway_payments
        }
        
        # Find matches and discrepancies
        matched = []
        local_only = []
        gateway_only = []
        discrepancies = []
        
        # Check local payments against gateway
        for local_payment in local_payments:
            charge_id = local_payment['provider_charge_id']
            if charge_id in gateway_lookup:
                gateway_payment = gateway_lookup[charge_id]
                
                # Check for discrepancies
                if self._has_discrepancy(local_payment, gateway_payment):
                    discrepancies.append({
                        'type': 'data_mismatch',
                        'local': local_payment,
                        'gateway': gateway_payment,
                        'differences': self._find_differences(local_payment, gateway_payment)
                    })
                else:
                    matched.append({
                        'local': local_payment,
                        'gateway': gateway_payment
                    })
            else:
                local_only.append(local_payment)
        
        # Check for gateway-only payments
        for gateway_payment in gateway_payments:
            charge_id = gateway_payment['provider_charge_id']
            if charge_id not in local_lookup:
                gateway_only.append(gateway_payment)
        
        return {
            'summary': {
                'total_local': len(local_payments),
                'total_gateway': len(gateway_payments),
                'matched': len(matched),
                'local_only': len(local_only),
                'gateway_only': len(gateway_only),
                'discrepancies': len(discrepancies)
            },
            'matched': matched,
            'local_only': local_only,
            'gateway_only': gateway_only,
            'discrepancies': discrepancies,
            'reconciliation_date': datetime.utcnow().isoformat()
        }
    
    def _has_discrepancy(
        self,
        local_payment: Dict[str, Any],
        gateway_payment: Dict[str, Any]
    ) -> bool:
        """Check if there are discrepancies between local and gateway payments."""
        return (
            local_payment['amount_minor'] != gateway_payment['amount_minor'] or
            local_payment['status'] != gateway_payment['status'] or
            local_payment['currency'] != gateway_payment['currency']
        )
    
    def _find_differences(
        self,
        local_payment: Dict[str, Any],
        gateway_payment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find specific differences between local and gateway payments."""
        differences = {}
        
        if local_payment['amount_minor'] != gateway_payment['amount_minor']:
            differences['amount'] = {
                'local': local_payment['amount_minor'],
                'gateway': gateway_payment['amount_minor'],
                'difference': local_payment['amount_minor'] - gateway_payment['amount_minor']
            }
        
        if local_payment['status'] != gateway_payment['status']:
            differences['status'] = {
                'local': local_payment['status'],
                'gateway': gateway_payment['status']
            }
        
        if local_payment['currency'] != gateway_payment['currency']:
            differences['currency'] = {
                'local': local_payment['currency'],
                'gateway': gateway_payment['currency']
            }
        
        return differences
    
    async def _log_reconciliation(self, reconciliation_result: Dict[str, Any]):
        """Log reconciliation results for audit purposes."""
        try:
            # Create audit log entry
            audit_log = AuditLog(
                actor="system",
                action="payment_reconciliation",
                resource_type="reconciliation",
                resource_id=str(uuid4()),
                metadata={
                    'summary': reconciliation_result['summary'],
                    'reconciliation_date': reconciliation_result['reconciliation_date']
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log reconciliation: {e}")
            # Don't raise here as it's not critical to the reconciliation process
    
    def detect_anomalies(
        self,
        start_date: datetime,
        end_date: datetime,
        threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect payment anomalies and suspicious patterns."""
        try:
            anomalies = []
            
            # Check for unusual payment amounts
            amount_anomalies = self._detect_amount_anomalies(start_date, end_date, threshold)
            anomalies.extend(amount_anomalies)
            
            # Check for unusual payment patterns
            pattern_anomalies = self._detect_pattern_anomalies(start_date, end_date)
            anomalies.extend(pattern_anomalies)
            
            # Check for failed payment clusters
            failure_anomalies = self._detect_failure_anomalies(start_date, end_date)
            anomalies.extend(failure_anomalies)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            raise ReconciliationError(f"Failed to detect anomalies: {e}")
    
    def _detect_amount_anomalies(
        self,
        start_date: datetime,
        end_date: datetime,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Detect payments with unusual amounts."""
        try:
            # Calculate average and standard deviation
            stats = self.db.query(
                func.avg(Charge.amount_minor).label('avg_amount'),
                func.stddev(Charge.amount_minor).label('std_amount')
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded'
                )
            ).first()
            
            if not stats.avg_amount or not stats.std_amount:
                return []
            
            avg_amount = float(stats.avg_amount)
            std_amount = float(stats.std_amount)
            
            # Find payments outside threshold
            threshold_amount = avg_amount + (threshold * std_amount)
            
            anomalies = self.db.query(Charge).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded',
                    Charge.amount_minor > threshold_amount
                )
            ).all()
            
            return [
                {
                    'type': 'unusual_amount',
                    'charge_id': str(anomaly.id),
                    'amount': anomaly.amount_minor,
                    'threshold': threshold_amount,
                    'deviation': (anomaly.amount_minor - avg_amount) / std_amount,
                    'created_at': anomaly.created_at.isoformat()
                }
                for anomaly in anomalies
            ]
            
        except Exception as e:
            logger.error(f"Failed to detect amount anomalies: {e}")
            return []
    
    def _detect_pattern_anomalies(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Detect unusual payment patterns."""
        try:
            anomalies = []
            
            # Check for rapid successive payments from same customer
            rapid_payments = self.db.query(
                Charge.customer_id,
                func.count(Charge.id).label('payment_count'),
                func.min(Charge.created_at).label('first_payment'),
                func.max(Charge.created_at).label('last_payment')
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded'
                )
            ).group_by(Charge.customer_id).having(
                func.count(Charge.id) >= 5
            ).all()
            
            for rapid in rapid_payments:
                time_span = rapid.last_payment - rapid.first_payment
                if time_span.total_seconds() < 3600:  # Less than 1 hour
                    anomalies.append({
                        'type': 'rapid_payments',
                        'customer_id': str(rapid.customer_id),
                        'payment_count': rapid.payment_count,
                        'time_span_seconds': time_span.total_seconds(),
                        'first_payment': rapid.first_payment.isoformat(),
                        'last_payment': rapid.last_payment.isoformat()
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect pattern anomalies: {e}")
            return []
    
    def _detect_failure_anomalies(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Detect clusters of failed payments."""
        try:
            # Check for customers with many failed payments
            failure_clusters = self.db.query(
                PaymentIntent.customer_id,
                func.count(PaymentIntent.id).label('failure_count')
            ).filter(
                and_(
                    PaymentIntent.created_at >= start_date,
                    PaymentIntent.created_at <= end_date,
                    PaymentIntent.status == 'canceled'
                )
            ).group_by(PaymentIntent.customer_id).having(
                func.count(PaymentIntent.id) >= 3
            ).all()
            
            return [
                {
                    'type': 'failure_cluster',
                    'customer_id': str(cluster.customer_id),
                    'failure_count': cluster.failure_count,
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    }
                }
                for cluster in failure_clusters
            ]
            
        except Exception as e:
            logger.error(f"Failed to detect failure anomalies: {e}")
            return []
    
    def generate_reconciliation_report(
        self,
        start_date: datetime,
        end_date: datetime,
        include_anomalies: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive reconciliation report."""
        try:
            # Perform reconciliation
            reconciliation = self.reconcile_payments(start_date, end_date)
            
            # Detect anomalies if requested
            anomalies = []
            if include_anomalies:
                anomalies = self.detect_anomalies(start_date, end_date)
            
            # Calculate financial summary
            financial_summary = self._calculate_financial_summary(start_date, end_date)
            
            return {
                'reconciliation': reconciliation,
                'anomalies': anomalies,
                'financial_summary': financial_summary,
                'report_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'include_anomalies': include_anomalies
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate reconciliation report: {e}")
            raise ReconciliationError(f"Failed to generate reconciliation report: {e}")
    
    def _calculate_financial_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate financial summary for the reconciliation period."""
        try:
            # Total charges
            total_charges = self.db.query(
                func.sum(Charge.amount_minor)
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded'
                )
            ).scalar() or 0
            
            # Total refunds
            total_refunds = self.db.query(
                func.sum(Refund.amount_minor)
            ).filter(
                and_(
                    Refund.created_at >= start_date,
                    Refund.created_at <= end_date
                )
            ).scalar() or 0
            
            # Net revenue
            net_revenue = total_charges - total_refunds
            
            # Payment method distribution
            payment_method_distribution = self.db.query(
                PaymentMethod.brand,
                func.sum(Charge.amount_minor).label('total_amount'),
                func.count(Charge.id).label('transaction_count')
            ).join(
                Charge, Charge.customer_id == PaymentMethod.customer_id
            ).filter(
                and_(
                    Charge.created_at >= start_date,
                    Charge.created_at <= end_date,
                    Charge.status == 'succeeded'
                )
            ).group_by(PaymentMethod.brand).all()
            
            return {
                'total_charges': total_charges,
                'total_refunds': total_refunds,
                'net_revenue': net_revenue,
                'total_charges_decimal': Decimal(total_charges) / 100,
                'total_refunds_decimal': Decimal(total_refunds) / 100,
                'net_revenue_decimal': Decimal(net_revenue) / 100,
                'payment_method_distribution': [
                    {
                        'brand': result.brand or 'unknown',
                        'total_amount': result.total_amount,
                        'total_amount_decimal': Decimal(result.total_amount) / 100,
                        'transaction_count': result.transaction_count
                    }
                    for result in payment_method_distribution
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate financial summary: {e}")
            return {}
