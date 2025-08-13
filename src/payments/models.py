"""Database models for the payment system."""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Boolean, ForeignKey, 
    UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

Base = declarative_base()


class Customer(Base):
    """Customer model for storing customer information."""
    
    __tablename__ = "customers"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    payment_methods: Mapped[list["PaymentMethod"]] = relationship(
        "PaymentMethod", back_populates="customer", cascade="all, delete-orphan"
    )
    payment_intents: Mapped[list["PaymentIntent"]] = relationship(
        "PaymentIntent", back_populates="customer", cascade="all, delete-orphan"
    )
    setup_intents: Mapped[list["SetupIntent"]] = relationship(
        "SetupIntent", back_populates="customer", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="customer", cascade="all, delete-orphan"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="customer", cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Customer(id={self.id}, email='{self.email}', country='{self.country}')>"


class Mandate(Base):
    """Mandate model for recurring payment authorization."""
    
    __tablename__ = "mandates"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_mandate_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    scheme: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    text_version: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    payment_methods: Mapped[list["PaymentMethod"]] = relationship(
        "PaymentMethod", back_populates="mandate", cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Mandate(id={self.id}, scheme='{self.scheme}', status='{self.status}')>"


class SetupIntent(Base):
    """Setup intent model for saving payment methods without charging."""
    
    __tablename__ = "setup_intents"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("customers.id"), 
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    client_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    payment_method_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="setup_intents")
    
    def __repr__(self):
        return f"<SetupIntent(id={self.id}, status='{self.status}', customer_id='{self.customer_id}')>"


class Subscription(Base):
    """Subscription model for recurring payments."""
    
    __tablename__ = "subscriptions"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("customers.id"), 
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    plan_id: Mapped[str] = mapped_column(String(100), nullable=False)
    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    interval: Mapped[str] = mapped_column(String(20), nullable=False)  # monthly, yearly, etc.
    interval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="subscriptions")
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="subscription", cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="subscription_amount_positive"),
        CheckConstraint("interval IN ('monthly', 'yearly', 'weekly', 'daily')", name="subscription_interval_valid"),
        CheckConstraint("status IN ('active', 'canceled', 'past_due', 'unpaid', 'trialing', 'incomplete', 'incomplete_expired')", name="subscription_status_valid"),
        Index("idx_subscription_customer_status", "customer_id", "status"),
        Index("idx_subscription_period", "current_period_end"),
    )
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, plan='{self.plan_name}', status='{self.status}')>"


class Invoice(Base):
    """Invoice model for billing and payment tracking."""
    
    __tablename__ = "invoices"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("customers.id"), 
        nullable=False
    )
    subscription_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("subscriptions.id"), 
        nullable=True
    )
    number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount_paid_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    amount_due_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="invoices")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="invoices")
    payment_intents: Mapped[list["PaymentIntent"]] = relationship(
        "PaymentIntent", back_populates="invoice", cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="invoice_amount_positive"),
        CheckConstraint("amount_paid_minor >= 0", name="invoice_amount_paid_non_negative"),
        CheckConstraint("amount_due_minor >= 0", name="invoice_amount_due_non_negative"),
        CheckConstraint("status IN ('draft', 'open', 'paid', 'void', 'uncollectible')", name="invoice_status_valid"),
        Index("idx_invoice_customer_status", "customer_id", "status"),
        Index("idx_invoice_due_date", "due_date"),
        Index("idx_invoice_number", "number"),
    )
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.number}', status='{self.status}')>"


class Dispute(Base):
    """Dispute model for payment disputes and chargebacks."""
    
    __tablename__ = "disputes"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    charge_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("charges.id"), 
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    evidence_due_by: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    charge: Mapped["Charge"] = relationship("Charge", back_populates="disputes")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="dispute_amount_positive"),
        CheckConstraint("status IN ('warning_needs_response', 'warning_under_review', 'needs_response', 'under_review', 'won', 'lost')", name="dispute_status_valid"),
        Index("idx_dispute_charge", "charge_id"),
        Index("idx_dispute_status", "status"),
        Index("idx_dispute_evidence_due", "evidence_due_by"),
    )
    
    def __repr__(self):
        return f"<Dispute(id={self.id}, reason='{self.reason}', status='{self.status}')>"


class PaymentMethod(Base):
    """Payment method model for storing customer payment methods."""
    
    __tablename__ = "payment_methods"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    pm_token: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    exp_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exp_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("customers.id"), 
        nullable=False
    )
    mandate_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("mandates.id"), 
        nullable=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="payment_methods")
    mandate: Mapped[Optional["Mandate"]] = relationship("Mandate", back_populates="payment_methods")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("exp_month >= 1 AND exp_month <= 12", name="exp_month_valid"),
        CheckConstraint("exp_year >= 2000", name="exp_year_valid"),
        Index("idx_payment_method_customer", "customer_id"),
        Index("idx_payment_method_default", "customer_id", "is_default"),
    )
    
    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, brand='{self.brand}', last4='{self.last4}')>"


class PaymentIntent(Base):
    """Payment intent model for tracking payment lifecycle."""
    
    __tablename__ = "payment_intents"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("customers.id"), 
        nullable=False
    )
    invoice_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("invoices.id"), 
        nullable=True
    )
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    capture_method: Mapped[str] = mapped_column(String(20), nullable=False)
    confirmation_method: Mapped[str] = mapped_column(String(20), nullable=False)
    three_ds_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="payment_intents")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="payment_intents")
    charges: Mapped[list["Charge"]] = relationship(
        "Charge", back_populates="payment_intent", cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="payment_intent_amount_positive"),
        CheckConstraint("capture_method IN ('automatic', 'manual')", name="payment_intent_capture_method_valid"),
        CheckConstraint("confirmation_method IN ('automatic', 'manual')", name="payment_intent_confirmation_method_valid"),
        CheckConstraint("status IN ('requires_payment_method', 'requires_confirmation', 'requires_action', 'processing', 'requires_capture', 'canceled', 'succeeded')", name="payment_intent_status_valid"),
        Index("idx_payment_intent_customer", "customer_id"),
        Index("idx_payment_intent_status", "status"),
        Index("idx_payment_intent_idempotency", "idempotency_key"),
    )
    
    def __repr__(self):
        return f"<PaymentIntent(id={self.id}, amount={self.amount_minor}, status='{self.status}')>"


class Charge(Base):
    """Charge model for completed payments."""
    
    __tablename__ = "charges"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    payment_intent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("payment_intents.id"), 
        nullable=False
    )
    provider_charge_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    failure_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    failure_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    payment_intent: Mapped["PaymentIntent"] = relationship("PaymentIntent", back_populates="charges")
    refunds: Mapped[list["Refund"]] = relationship(
        "Refund", back_populates="charge", cascade="all, delete-orphan"
    )
    disputes: Mapped[list["Dispute"]] = relationship(
        "Dispute", back_populates="charge", cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('succeeded', 'pending', 'failed', 'canceled')", name="charge_status_valid"),
        Index("idx_charge_payment_intent", "payment_intent_id"),
        Index("idx_charge_status", "status"),
    )
    
    def __repr__(self):
        return f"<Charge(id={self.id}, status='{self.status}')>"


class Refund(Base):
    """Refund model for payment refunds."""
    
    __tablename__ = "refunds"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    charge_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("charges.id"), 
        nullable=False
    )
    provider_refund_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    charge: Mapped["Charge"] = relationship("Charge", back_populates="refunds")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            amount_minor > 0, 
            name="check_refund_amount_positive"
        ),
        CheckConstraint(
            status.in_(["pending", "succeeded", "failed"]), 
            name="check_refund_status_valid"
        ),
    )
    
    def __repr__(self):
        return f"<Refund(id={self.id}, amount={self.amount_minor}, status='{self.status}')>"


class WebhookEvent(Base):
    """Webhook event model for tracking webhook processing."""
    
    __tablename__ = "webhook_events"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(20), 
        server_default="pending", 
        nullable=False
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            processing_status.in_(["pending", "processing", "completed", "failed"]), 
            name="check_webhook_status_valid"
        ),
    )
    
    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, type='{self.type}', status='{self.processing_status}')>"


class AuditLog(Base):
    """Audit log model for tracking payment system actions."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"


# Create indexes for performance
def create_indexes(engine):
    """Create database indexes for optimal performance."""
    from sqlalchemy import text
    
    indexes = [
        # Payment intents
        "CREATE INDEX IF NOT EXISTS idx_payment_intents_customer_id ON payment_intents(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_payment_intents_status ON payment_intents(status)",
        "CREATE INDEX IF NOT EXISTS idx_payment_intents_created_at ON payment_intents(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_payment_intents_invoice_id ON payment_intents(invoice_id)",
        
        # Charges
        "CREATE INDEX IF NOT EXISTS idx_charges_payment_intent_id ON charges(payment_intent_id)",
        "CREATE INDEX IF NOT EXISTS idx_charges_status ON charges(status)",
        
        # Refunds
        "CREATE INDEX IF NOT EXISTS idx_refunds_charge_id ON refunds(charge_id)",
        "CREATE INDEX IF NOT EXISTS idx_refunds_status ON refunds(status)",
        
        # Subscriptions
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_id ON subscriptions(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON subscriptions(current_period_end)",
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id ON subscriptions(plan_id)",
        
        # Invoices
        "CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_subscription_id ON invoices(subscription_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(number)",
        
        # Payment methods
        "CREATE INDEX IF NOT EXISTS idx_payment_methods_customer_id ON payment_methods(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_payment_methods_default ON payment_methods(customer_id, is_default)",
        
        # Disputes
        "CREATE INDEX IF NOT EXISTS idx_disputes_charge_id ON disputes(charge_id)",
        "CREATE INDEX IF NOT EXISTS idx_disputes_status ON disputes(status)",
        "CREATE INDEX IF NOT EXISTS idx_disputes_evidence_due ON disputes(evidence_due_by)",
        
        # Webhook events
        "CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON webhook_events(type)",
        "CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON webhook_events(processing_status)",
        "CREATE INDEX IF NOT EXISTS idx_webhook_events_provider ON webhook_events(provider)",
        
        # Audit logs
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor)",
    ]
    
    for index_sql in indexes:
        try:
            engine.execute(text(index_sql))
        except Exception as e:
            # Log index creation errors but don't fail
            print(f"Warning: Failed to create index: {e}")
