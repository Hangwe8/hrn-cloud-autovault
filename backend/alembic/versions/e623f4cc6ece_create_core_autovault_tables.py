"""Create core AutoVault tables

Revision ID: e623f4cc6ece
Revises:
Create Date: 2026-09-19 17:14:31.116212
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e623f4cc6ece"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all core AutoVault tables."""

    # ------------------------------------------------------------------
    # Businesses
    # ------------------------------------------------------------------
    # This table must be created first because customers, users, and
    # vehicles all reference businesses.id.
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_businesses_id"),
        "businesses",
        ["id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_customers_id"),
        "customers",
        ["id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_users_id"),
        "users",
        ["id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Vehicles
    # ------------------------------------------------------------------
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("registration", sa.String(length=30), nullable=False),
        sa.Column("vin", sa.String(length=50), nullable=True),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_vehicles_id"),
        "vehicles",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop all core AutoVault tables."""

    # Vehicles depends on both customers and businesses,
    # so it must be dropped first.
    op.drop_index(
        op.f("ix_vehicles_id"),
        table_name="vehicles",
    )
    op.drop_table("vehicles")

    # Users depends on businesses.
    op.drop_index(
        op.f("ix_users_id"),
        table_name="users",
    )
    op.drop_table("users")

    # Customers depends on businesses.
    op.drop_index(
        op.f("ix_customers_id"),
        table_name="customers",
    )
    op.drop_table("customers")

    # Businesses is the parent table, so it is dropped last.
    op.drop_index(
        op.f("ix_businesses_id"),
        table_name="businesses",
    )
    op.drop_table("businesses")