"""Add payment system tables

Revision ID: 0002_payments_schema
Revises: 0001_initial_schema
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_payments_schema'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create customers table
    op.create_table('customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id'),
        sa.UniqueConstraint('email')
    )
    
    # Create payment_methods table
    op.create_table('payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('pm_token', sa.String(length=255), nullable=False),
        sa.Column('brand', sa.String(length=50), nullable=True),
        sa.Column('last4', sa.String(length=4), nullable=True),
        sa.Column('exp_month', sa.Integer(), nullable=True),
        sa.Column('exp_year', sa.Integer(), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mandate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['mandate_id'], ['mandates.id'], )
    )
    
    # Create mandates table
    op.create_table('mandates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_mandate_id', sa.String(length=255), nullable=False),
        sa.Column('scheme', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('text_version', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_mandate_id')
    )
    
    # Create payment_intents table
    op.create_table('payment_intents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', sa.String(length=255), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_minor', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('capture_method', sa.String(length=20), nullable=False),
        sa.Column('confirmation_method', sa.String(length=20), nullable=False),
        sa.Column('three_ds_status', sa.String(length=50), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.UniqueConstraint('idempotency_key')
    )
    
    # Create charges table
    op.create_table('charges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_intent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_charge_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['payment_intent_id'], ['payment_intents.id'], ),
        sa.UniqueConstraint('provider_charge_id')
    )
    
    # Create refunds table
    op.create_table('refunds',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('charge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_refund_id', sa.String(length=255), nullable=False),
        sa.Column('amount_minor', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['charge_id'], ['charges.id'], ),
        sa.UniqueConstraint('provider_refund_id')
    )
    
    # Create webhook_events table
    op.create_table('webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_payment_intents_customer_id', 'payment_intents', ['customer_id'])
    op.create_index('idx_payment_intents_status', 'payment_intents', ['status'])
    op.create_index('idx_payment_intents_created_at', 'payment_intents', ['created_at'])
    op.create_index('idx_charges_payment_intent_id', 'charges', ['payment_intent_id'])
    op.create_index('idx_refunds_charge_id', 'refunds', ['charge_id'])
    op.create_index('idx_webhook_events_type', 'webhook_events', ['type'])
    op.create_index('idx_webhook_events_status', 'webhook_events', ['processing_status'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_resource', table_name='audit_logs')
    op.drop_index('idx_webhook_events_status', table_name='webhook_events')
    op.drop_index('idx_webhook_events_type', table_name='webhook_events')
    op.drop_index('idx_refunds_charge_id', table_name='refunds')
    op.drop_index('idx_charges_payment_intent_id', table_name='charges')
    op.drop_index('idx_payment_intents_created_at', table_name='payment_intents')
    op.drop_index('idx_payment_intents_status', table_name='payment_intents')
    op.drop_index('idx_payment_intents_customer_id', table_name='payment_intents')
    
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('webhook_events')
    op.drop_table('refunds')
    op.drop_table('charges')
    op.drop_table('payment_intents')
    op.drop_table('mandates')
    op.drop_table('payment_methods')
    op.drop_table('customers')
