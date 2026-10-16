"""Make the items table.

Revision ID: 0001
Revises:
Create Date: 2026-10-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make the items table and the index on the SKU column."""
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sku", sa.String(length=40), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False, server_default="general"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("sku", name="uq_items_sku"),
    )
    op.create_index("ix_items_sku", "items", ["sku"])
    op.create_index("ix_items_category", "items", ["category"])


def downgrade() -> None:
    """Remove the items table."""
    op.drop_index("ix_items_category", table_name="items")
    op.drop_index("ix_items_sku", table_name="items")
    op.drop_table("items")
