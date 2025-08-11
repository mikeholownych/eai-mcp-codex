"""Subscription service for managing recurring payments and billing."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import Subscription, Invoice, Customer, PaymentIntent
from .exceptions import SubscriptionError, BillingError
from .gateways.base import PaymentGateway
from .utils import generate_invoice_number, calculate_proration

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing subscriptions and recurring billing."""
    
    def __init__(self, db: Session, payment_gateway: PaymentGateway):
        self.db = db
        self.payment_gateway = payment_gateway
    
    def create_subscription(
        self,
        customer_id: UUID,
        plan_id: str,
        plan_name: str,
        amount: int,
        currency: str,
        interval: str,
        interval_count: int = 1,
        trial_days: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """Create a new subscription for a customer."""
        try:
            # Create subscription in payment gateway
            gateway_subscription = self.payment_gateway.create_subscription(
                customer_id=str(customer_id),
                plan_id=plan_id,
                amount=amount,
                currency=currency,
                interval=interval,
                interval_count=interval_count,
                trial_days=trial_days,
                metadata=metadata
            )
            
            # Create local subscription record
            subscription = Subscription(
                provider_id=gateway_subscription.id,
                customer_id=customer_id,
                status="active" if trial_days == 0 else "trialing",
                plan_id=plan_id,
                plan_name=plan_name,
                interval=interval,
                interval_count=interval_count,
                amount=amount,
                currency=currency,
                trial_start=datetime.utcnow() if trial_days > 0 else None,
                trial_end=datetime.utcnow() + timedelta(days=trial_days) if trial_days > 0 else None,
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + self._calculate_interval_delta(interval, interval_count),
                metadata=metadata or {}
            )
            
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)
            
            logger.info(f"Created subscription {subscription.id} for customer {customer_id}")
            return subscription
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create subscription: {e}")
            raise SubscriptionError(f"Failed to create subscription: {e}")
    
    def cancel_subscription(
        self,
        subscription_id: UUID,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None
    ) -> Subscription:
        """Cancel a subscription."""
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise SubscriptionError(f"Subscription {subscription_id} not found")
        
        try:
            # Cancel in payment gateway
            self.payment_gateway.cancel_subscription(
                subscription.provider_id,
                cancel_at_period_end=cancel_at_period_end
            )
            
            if cancel_at_period_end:
                subscription.status = "canceled"
                subscription.canceled_at = datetime.utcnow()
                subscription.cancel_at_period_end = True
                subscription.cancellation_reason = reason
            else:
                subscription.status = "canceled"
                subscription.canceled_at = datetime.utcnow()
                subscription.cancel_at_period_end = False
                subscription.cancellation_reason = reason
            
            self.db.commit()
            self.db.refresh(subscription)
            
            logger.info(f"Canceled subscription {subscription_id}")
            return subscription
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cancel subscription: {e}")
            raise SubscriptionError(f"Failed to cancel subscription: {e}")
    
    def update_subscription(
        self,
        subscription_id: UUID,
        plan_id: Optional[str] = None,
        amount: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """Update subscription details."""
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise SubscriptionError(f"Subscription {subscription_id} not found")
        
        try:
            # Update in payment gateway
            gateway_subscription = self.payment_gateway.update_subscription(
                subscription.provider_id,
                plan_id=plan_id,
                amount=amount,
                metadata=metadata
            )
            
            # Update local record
            if plan_id:
                subscription.plan_id = plan_id
            if amount:
                subscription.amount = amount
            if metadata:
                subscription.metadata.update(metadata)
            
            self.db.commit()
            self.db.refresh(subscription)
            
            logger.info(f"Updated subscription {subscription_id}")
            return subscription
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update subscription: {e}")
            raise SubscriptionError(f"Failed to update subscription: {e}")
    
    def process_subscription_renewal(self, subscription_id: UUID) -> Invoice:
        """Process a subscription renewal and create an invoice."""
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise SubscriptionError(f"Subscription {subscription_id} not found")
        
        if subscription.status not in ["active", "trialing"]:
            raise SubscriptionError(f"Subscription {subscription_id} is not active")
        
        try:
            # Create invoice
            invoice = Invoice(
                customer_id=subscription.customer_id,
                subscription_id=subscription_id,
                amount=subscription.amount,
                currency=subscription.currency,
                status="draft",
                due_date=datetime.utcnow(),
                invoice_number=generate_invoice_number(),
                description=f"Subscription renewal for {subscription.plan_name}",
                metadata={"subscription_id": str(subscription_id)}
            )
            
            self.db.add(invoice)
            self.db.commit()
            self.db.refresh(invoice)
            
            # Update subscription period
            subscription.current_period_start = subscription.current_period_end
            subscription.current_period_end = subscription.current_period_start + self._calculate_interval_delta(
                subscription.interval, subscription.interval_count
            )
            
            # Handle trial expiration
            if subscription.status == "trialing" and subscription.trial_end and subscription.trial_end <= datetime.utcnow():
                subscription.status = "active"
                subscription.trial_end = None
            
            self.db.commit()
            self.db.refresh(subscription)
            
            logger.info(f"Processed renewal for subscription {subscription_id}, created invoice {invoice.id}")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to process subscription renewal: {e}")
            raise SubscriptionError(f"Failed to process subscription renewal: {e}")
    
    def get_subscriptions_by_customer(self, customer_id: UUID) -> List[Subscription]:
        """Get all subscriptions for a customer."""
        return self.db.query(Subscription).filter(
            Subscription.customer_id == customer_id
        ).order_by(Subscription.created_at.desc()).all()
    
    def get_active_subscriptions(self) -> List[Subscription]:
        """Get all active subscriptions."""
        return self.db.query(Subscription).filter(
            Subscription.status.in_(["active", "trialing"])
        ).all()
    
    def get_subscriptions_due_for_renewal(self, days_ahead: int = 1) -> List[Subscription]:
        """Get subscriptions due for renewal within specified days."""
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        return self.db.query(Subscription).filter(
            and_(
                Subscription.status.in_(["active", "trialing"]),
                Subscription.current_period_end <= cutoff_date
            )
        ).all()
    
    def _calculate_interval_delta(self, interval: str, interval_count: int) -> timedelta:
        """Calculate the time delta for a given interval."""
        if interval == "day":
            return timedelta(days=interval_count)
        elif interval == "week":
            return timedelta(weeks=interval_count)
        elif interval == "month":
            return timedelta(days=30 * interval_count)  # Approximate
        elif interval == "year":
            return timedelta(days=365 * interval_count)  # Approximate
        else:
            raise ValueError(f"Unsupported interval: {interval}")


class BillingService:
    """Service for managing invoices and billing operations."""
    
    def __init__(self, db: Session, payment_gateway: PaymentGateway):
        self.db = db
        self.payment_gateway = payment_gateway
    
    def create_invoice(
        self,
        customer_id: UUID,
        amount: int,
        currency: str,
        description: str,
        due_date: Optional[datetime] = None,
        subscription_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Invoice:
        """Create a new invoice."""
        try:
            invoice = Invoice(
                customer_id=customer_id,
                subscription_id=subscription_id,
                amount=amount,
                currency=currency,
                status="draft",
                due_date=due_date or datetime.utcnow(),
                invoice_number=generate_invoice_number(),
                description=description,
                metadata=metadata or {}
            )
            
            self.db.add(invoice)
            self.db.commit()
            self.db.refresh(invoice)
            
            logger.info(f"Created invoice {invoice.id} for customer {customer_id}")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create invoice: {e}")
            raise BillingError(f"Failed to create invoice: {e}")
    
    def finalize_invoice(self, invoice_id: UUID) -> Invoice:
        """Finalize an invoice and make it payable."""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise BillingError(f"Invoice {invoice_id} not found")
        
        if invoice.status != "draft":
            raise BillingError(f"Invoice {invoice_id} is not in draft status")
        
        try:
            invoice.status = "open"
            invoice.finalized_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(invoice)
            
            logger.info(f"Finalized invoice {invoice_id}")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to finalize invoice: {e}")
            raise BillingError(f"Failed to finalize invoice: {e}")
    
    def mark_invoice_paid(self, invoice_id: UUID, payment_intent_id: UUID) -> Invoice:
        """Mark an invoice as paid."""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise BillingError(f"Invoice {invoice_id} not found")
        
        try:
            invoice.status = "paid"
            invoice.paid_at = datetime.utcnow()
            invoice.payment_intent_id = payment_intent_id
            
            self.db.commit()
            self.db.refresh(invoice)
            
            logger.info(f"Marked invoice {invoice_id} as paid")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to mark invoice as paid: {e}")
            raise BillingError(f"Failed to mark invoice as paid: {e}")
    
    def get_invoices_by_customer(self, customer_id: UUID) -> List[Invoice]:
        """Get all invoices for a customer."""
        return self.db.query(Invoice).filter(
            Invoice.customer_id == customer_id
        ).order_by(Invoice.created_at.desc()).all()
    
    def get_overdue_invoices(self) -> List[Invoice]:
        """Get all overdue invoices."""
        return self.db.query(Invoice).filter(
            and_(
                Invoice.status == "open",
                Invoice.due_date < datetime.utcnow()
            )
        ).all()
