"""add till_shifts table

Revision ID: ee59b6fce6e4
Revises: 308fd99b1dc6
Create Date: 2026-03-20 15:38:04.982281
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee59b6fce6e4'
down_revision = '308fd99b1dc6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'till_shifts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('branch_id', sa.UUID(), nullable=False),
        sa.Column('till_id', sa.UUID(), nullable=False),
        sa.Column('cashier_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('opening_float', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0'),
        sa.Column('closing_cash', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('till_shifts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_till_shifts_branch_id'), ['branch_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_till_shifts_cashier_id'), ['cashier_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_till_shifts_closed_at'), ['closed_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_till_shifts_opened_at'), ['opened_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_till_shifts_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_till_shifts_tenant_id'), ['tenant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_till_shifts_till_id'), ['till_id'], unique=False)


def downgrade():
    with op.batch_alter_table('till_shifts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_till_shifts_till_id'))
        batch_op.drop_index(batch_op.f('ix_till_shifts_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_till_shifts_status'))
        batch_op.drop_index(batch_op.f('ix_till_shifts_opened_at'))
        batch_op.drop_index(batch_op.f('ix_till_shifts_closed_at'))
        batch_op.drop_index(batch_op.f('ix_till_shifts_cashier_id'))
        batch_op.drop_index(batch_op.f('ix_till_shifts_branch_id'))

    op.drop_table('till_shifts')