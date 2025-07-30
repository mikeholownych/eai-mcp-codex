"""Initial core schema."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create core tables and indexes."""
    op.create_table(
        "service_registry",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("service_name", sa.String(100), nullable=False),
        sa.Column("service_url", sa.String(255), nullable=False),
        sa.Column("health_status", sa.String(20), server_default="unknown"),
        sa.Column(
            "last_heartbeat",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("metadata", sa.JSON(), server_default=sa.text("'{}'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_service_registry_name", "service_registry", ["service_name"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("service_name", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.String(100)),
        sa.Column("user_id", sa.String(100)),
        sa.Column("details", sa.JSON()),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_audit_log_service", "audit_log", ["service_name"])
    op.create_index("idx_audit_log_timestamp", "audit_log", ["timestamp"])

    op.create_table(
        "metrics_summary",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Numeric()),
        sa.Column("labels", sa.JSON(), server_default=sa.text("'{}'")),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_metrics_summary_name", "metrics_summary", ["metric_name"])
    op.create_index("idx_metrics_summary_timestamp", "metrics_summary", ["timestamp"])


def downgrade() -> None:
    """Drop core tables and indexes."""
    op.drop_index("idx_metrics_summary_timestamp", table_name="metrics_summary")
    op.drop_index("idx_metrics_summary_name", table_name="metrics_summary")
    op.drop_table("metrics_summary")

    op.drop_index("idx_audit_log_timestamp", table_name="audit_log")
    op.drop_index("idx_audit_log_service", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("idx_service_registry_name", table_name="service_registry")
    op.drop_table("service_registry")
