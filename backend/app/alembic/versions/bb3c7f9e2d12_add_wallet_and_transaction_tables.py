"""
Add wallet and transaction tables.

Revision ID: bb3c7f9e2d12
Revises: 1a31ce608336
Create Date: 2025-09-16 20:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bb3c7f9e2d12"
down_revision = "1a31ce608336"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create wallet table
    op.create_table(
        "wallet",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "balance",
            sa.DECIMAL(precision=10, scale=2),
            nullable=False,
            default="0.00",
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_wallet_user_id"), "wallet", ["user_id"], unique=False)
    op.create_index(op.f("ix_wallet_currency"), "wallet", ["currency"], unique=False)

    # Create transaction table
    op.create_table(
        "transaction",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "wallet_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.DECIMAL(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.String(length=6),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.text("NOW()"),
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["wallet_id"],
            ["wallet.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_transaction_wallet_id"), "transaction", ["wallet_id"], unique=False
    )
    op.create_index(
        op.f("ix_transaction_timestamp"), "transaction", ["timestamp"], unique=False
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop transaction table
    op.drop_index(op.f("ix_transaction_timestamp"), table_name="transaction")
    op.drop_index(op.f("ix_transaction_wallet_id"), table_name="transaction")
    op.drop_table("transaction")

    # Drop wallet table
    op.drop_index(op.f("ix_wallet_currency"), table_name="wallet")
    op.drop_index(op.f("ix_wallet_user_id"), table_name="wallet")
    op.drop_table("wallet")
