"""
Add wallet and transaction tables.

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2025-09-16 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "1a31ce608336"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create wallet table
    op.create_table(
        "wallet",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("balance", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create transaction table
    op.create_table(
        "transaction",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("transaction_type", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["wallet_id"],
            ["wallet.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table("transaction")
    op.drop_table("wallet")
