"""Create auth service schema

Revision ID: 0003_auth_service_schema
Revises: 0002_multi_developer_coordination
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers
revision = '0003_auth_service_schema'
down_revision = '0002_multi_developer_coordination'
branch_labels = None
depends_on = None


def upgrade():
    """Create auth service tables."""
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

    # User roles table
    op.create_table(
        'user_roles',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    # API keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_hash', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('key_prefix', sa.String(12), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    # Revoked tokens table (for JWT blacklist)
    op.create_table(
        'revoked_tokens',
        sa.Column('jti', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Password reset tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('is_used', sa.Boolean(), default=False, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    # User sessions table (for session management)
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_token', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    # Audit log table for security events
    op.create_table(
        'auth_audit_log',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),  # login, logout, password_change, etc.
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    # Create indexes for performance
    op.create_index('idx_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_revoked_tokens_user_id', 'revoked_tokens', ['user_id'])
    op.create_index('idx_revoked_tokens_expires_at', 'revoked_tokens', ['expires_at'])
    op.create_index('idx_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    op.create_index('idx_auth_audit_log_user_id', 'auth_audit_log', ['user_id'])
    op.create_index('idx_auth_audit_log_event_type', 'auth_audit_log', ['event_type'])
    op.create_index('idx_auth_audit_log_created_at', 'auth_audit_log', ['created_at'])


def downgrade():
    """Drop auth service tables."""
    
    # Drop indexes first
    op.drop_index('idx_auth_audit_log_created_at')
    op.drop_index('idx_auth_audit_log_event_type')
    op.drop_index('idx_auth_audit_log_user_id')
    op.drop_index('idx_user_sessions_expires_at')
    op.drop_index('idx_user_sessions_user_id')
    op.drop_index('idx_password_reset_tokens_expires_at')
    op.drop_index('idx_password_reset_tokens_user_id')
    op.drop_index('idx_revoked_tokens_expires_at')
    op.drop_index('idx_revoked_tokens_user_id')
    op.drop_index('idx_api_keys_user_id')
    op.drop_index('idx_user_roles_user_id')
    
    # Drop tables
    op.drop_table('auth_audit_log')
    op.drop_table('user_sessions')
    op.drop_table('password_reset_tokens')
    op.drop_table('revoked_tokens')
    op.drop_table('api_keys')
    op.drop_table('user_roles')
    op.drop_table('users')