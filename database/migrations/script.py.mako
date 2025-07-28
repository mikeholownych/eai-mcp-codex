<%text>
Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
</%text>

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    """Create the initial example table."""
    op.create_table(
        "example",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
    )


def downgrade() -> None:
    """Drop the example table."""
    op.drop_table("example")
