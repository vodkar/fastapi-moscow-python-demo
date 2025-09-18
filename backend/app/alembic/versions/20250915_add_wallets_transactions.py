"""
Add wallet and transaction tables.

Revision ID: 20250915_add_wallets_transactions
Revises: 1a31ce608336
Create Date: 2025-09-15

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250915_add_wallets_transactions"
down_revision = "1a31ce608336"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "wallet",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(length=255), nullable=False),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "currency", name="uq_wallet_user_currency"),
    )

    transaction_type = sa.Enum("credit", "debit", name="transaction_type")
    transaction_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "transaction",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("type", transaction_type, nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("currency", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallet.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("transaction")
    op.drop_table("wallet")
    sa.Enum(name="transaction_type").drop(op.get_bind(), checkfirst=True)
