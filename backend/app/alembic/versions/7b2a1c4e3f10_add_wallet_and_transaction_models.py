"""
Add wallet and transaction models.

Revision ID: 7b2a1c4e3f10
Revises: 1a31ce608336
Create Date: 2025-09-16 06:30:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7b2a1c4e3f10"
down_revision = "1a31ce608336"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Upgrade database schema by creating wallet and transaction tables."""
    # Ensure uuid extension exists (PostgreSQL)
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "wallet",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_wallet_user_id", "wallet", ["user_id"], unique=False)

    op.create_table(
        "transaction",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column(
            "timestamp",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallet.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_transaction_wallet_id", "transaction", ["wallet_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade database schema by dropping new tables."""
    op.drop_index("ix_transaction_wallet_id", table_name="transaction")
    op.drop_table("transaction")
    op.drop_index("ix_wallet_user_id", table_name="wallet")
    op.drop_table("wallet")
