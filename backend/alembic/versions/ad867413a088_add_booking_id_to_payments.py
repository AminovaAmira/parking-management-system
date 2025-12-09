"""add_booking_id_to_payments

Revision ID: ad867413a088
Revises: 8c64ecd615bf
Create Date: 2025-12-09 12:26:07.213571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad867413a088'
down_revision: Union[str, None] = '8c64ecd615bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add booking_id column
    op.add_column('payments', sa.Column('booking_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_payments_booking_id'), 'payments', ['booking_id'], unique=False)
    op.create_foreign_key('fk_payments_booking_id', 'payments', 'bookings', ['booking_id'], ['booking_id'])

    # Make session_id nullable
    op.alter_column('payments', 'session_id', nullable=True)

    # Update payment_method default
    op.alter_column('payments', 'payment_method', server_default='pending')


def downgrade() -> None:
    # Revert payment_method default
    op.alter_column('payments', 'payment_method', server_default=None)

    # Make session_id not nullable again
    op.alter_column('payments', 'session_id', nullable=False)

    # Drop booking_id column
    op.drop_constraint('fk_payments_booking_id', 'payments', type_='foreignkey')
    op.drop_index(op.f('ix_payments_booking_id'), table_name='payments')
    op.drop_column('payments', 'booking_id')
