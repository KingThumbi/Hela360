"""standardize till shift identifiers to string36

Revision ID: a890db1a5691
Revises: c546daa8819b
Create Date: 2026-08-17 22:54:51.369432

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a890db1a5691"
down_revision = "c546daa8819b"
branch_labels = None
depends_on = None


# =============================================================================
# Constraint Names
# =============================================================================

FK_SALES_TILL_SHIFT = (
    "fk_sales_till_shift_id_till_shifts"
)

FK_REFUNDS_TILL_SHIFT = (
    "fk_sale_refunds_till_shift_id_till_shifts"
)

FK_TILL_SHIFT_TENANT = (
    "fk_till_shifts_tenant_id_tenants"
)

FK_TILL_SHIFT_BRANCH = (
    "fk_till_shifts_branch_id_branches"
)

FK_TILL_SHIFT_TILL = (
    "fk_till_shifts_till_id_tills"
)

FK_TILL_SHIFT_CASHIER = (
    "fk_till_shifts_cashier_id_users"
)


def upgrade():
    """
    Standardize TillShift identifiers on Hela360's canonical
    UUID-formatted String(36) representation.

    Existing UUID values are preserved in place using explicit
    PostgreSQL UUID -> VARCHAR casts.
    """

    # -------------------------------------------------------------------------
    # 1. Drop dependent foreign keys.
    #
    # PostgreSQL cannot safely change the referenced till_shifts.id type while
    # sales and sale_refunds still reference it using UUID foreign keys.
    # -------------------------------------------------------------------------

    op.drop_constraint(
        FK_SALES_TILL_SHIFT,
        "sales",
        type_="foreignkey",
    )

    op.drop_constraint(
        FK_REFUNDS_TILL_SHIFT,
        "sale_refunds",
        type_="foreignkey",
    )

    # -------------------------------------------------------------------------
    # 2. Convert TillShift aggregate identifiers.
    # -------------------------------------------------------------------------

    op.alter_column(
        "till_shifts",
        "id",
        existing_type=sa.UUID(),
        type_=sa.String(length=36),
        existing_nullable=False,
        postgresql_using="id::text",
    )

    op.alter_column(
        "till_shifts",
        "tenant_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=36),
        existing_nullable=False,
        postgresql_using="tenant_id::text",
    )

    op.alter_column(
        "till_shifts",
        "branch_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=36),
        existing_nullable=False,
        postgresql_using="branch_id::text",
    )

    op.alter_column(
        "till_shifts",
        "till_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=36),
        existing_nullable=False,
        postgresql_using="till_id::text",
    )

    op.alter_column(
        "till_shifts",
        "cashier_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=36),
        existing_nullable=False,
        postgresql_using="cashier_id::text",
    )

    # -------------------------------------------------------------------------
    # 3. Convert dependent attribution columns.
    # -------------------------------------------------------------------------

    op.alter_column(
        "sales",
        "till_shift_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=36),
        existing_nullable=True,
        postgresql_using="till_shift_id::text",
    )

    op.alter_column(
        "sale_refunds",
        "till_shift_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=36),
        existing_nullable=True,
        postgresql_using="till_shift_id::text",
    )

    # -------------------------------------------------------------------------
    # 4. Add canonical TillShift domain foreign keys.
    #
    # These were previously impossible because TillShift used PostgreSQL UUID
    # columns while the referenced Hela360 models use VARCHAR(36).
    # -------------------------------------------------------------------------

    op.create_foreign_key(
        FK_TILL_SHIFT_TENANT,
        "till_shifts",
        "tenants",
        ["tenant_id"],
        ["id"],
    )

    op.create_foreign_key(
        FK_TILL_SHIFT_BRANCH,
        "till_shifts",
        "branches",
        ["branch_id"],
        ["id"],
    )

    op.create_foreign_key(
        FK_TILL_SHIFT_TILL,
        "till_shifts",
        "tills",
        ["till_id"],
        ["id"],
    )

    op.create_foreign_key(
        FK_TILL_SHIFT_CASHIER,
        "till_shifts",
        "users",
        ["cashier_id"],
        ["id"],
    )

    # -------------------------------------------------------------------------
    # 5. Restore dependent foreign keys.
    # -------------------------------------------------------------------------

    op.create_foreign_key(
        FK_SALES_TILL_SHIFT,
        "sales",
        "till_shifts",
        ["till_shift_id"],
        ["id"],
    )

    op.create_foreign_key(
        FK_REFUNDS_TILL_SHIFT,
        "sale_refunds",
        "till_shifts",
        ["till_shift_id"],
        ["id"],
    )


def downgrade():
    """
    Restore the former native PostgreSQL UUID TillShift representation.

    This assumes all identifier values remain valid UUID-formatted strings,
    which is consistent with Hela360's identifier generation strategy.
    """

    # -------------------------------------------------------------------------
    # 1. Remove dependent foreign keys.
    # -------------------------------------------------------------------------

    op.drop_constraint(
        FK_SALES_TILL_SHIFT,
        "sales",
        type_="foreignkey",
    )

    op.drop_constraint(
        FK_REFUNDS_TILL_SHIFT,
        "sale_refunds",
        type_="foreignkey",
    )

    # -------------------------------------------------------------------------
    # 2. Remove String(36) TillShift domain foreign keys before changing types.
    # -------------------------------------------------------------------------

    op.drop_constraint(
        FK_TILL_SHIFT_CASHIER,
        "till_shifts",
        type_="foreignkey",
    )

    op.drop_constraint(
        FK_TILL_SHIFT_TILL,
        "till_shifts",
        type_="foreignkey",
    )

    op.drop_constraint(
        FK_TILL_SHIFT_BRANCH,
        "till_shifts",
        type_="foreignkey",
    )

    op.drop_constraint(
        FK_TILL_SHIFT_TENANT,
        "till_shifts",
        type_="foreignkey",
    )

    # -------------------------------------------------------------------------
    # 3. Convert dependent columns back to native UUID.
    # -------------------------------------------------------------------------

    op.alter_column(
        "sales",
        "till_shift_id",
        existing_type=sa.String(length=36),
        type_=sa.UUID(),
        existing_nullable=True,
        postgresql_using="till_shift_id::uuid",
    )

    op.alter_column(
        "sale_refunds",
        "till_shift_id",
        existing_type=sa.String(length=36),
        type_=sa.UUID(),
        existing_nullable=True,
        postgresql_using="till_shift_id::uuid",
    )

    # -------------------------------------------------------------------------
    # 4. Convert TillShift aggregate identifiers back to native UUID.
    # -------------------------------------------------------------------------

    op.alter_column(
        "till_shifts",
        "cashier_id",
        existing_type=sa.String(length=36),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="cashier_id::uuid",
    )

    op.alter_column(
        "till_shifts",
        "till_id",
        existing_type=sa.String(length=36),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="till_id::uuid",
    )

    op.alter_column(
        "till_shifts",
        "branch_id",
        existing_type=sa.String(length=36),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="branch_id::uuid",
    )

    op.alter_column(
        "till_shifts",
        "tenant_id",
        existing_type=sa.String(length=36),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="tenant_id::uuid",
    )

    op.alter_column(
        "till_shifts",
        "id",
        existing_type=sa.String(length=36),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="id::uuid",
    )

    # -------------------------------------------------------------------------
    # 5. Restore legacy UUID attribution foreign keys.
    # -------------------------------------------------------------------------

    op.create_foreign_key(
        FK_SALES_TILL_SHIFT,
        "sales",
        "till_shifts",
        ["till_shift_id"],
        ["id"],
    )

    op.create_foreign_key(
        FK_REFUNDS_TILL_SHIFT,
        "sale_refunds",
        "till_shifts",
        ["till_shift_id"],
        ["id"],
    )