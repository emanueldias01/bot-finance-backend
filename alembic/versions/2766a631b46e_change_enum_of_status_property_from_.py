"""change enum of status property from open finance connection table

Revision ID: 2766a631b46e
Revises: 4a442c9258ee
Create Date: 2026-06-13 00:46:11.571426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2766a631b46e'
down_revision: Union[str, Sequence[str], None] = '4a442c9258ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create new enum type
    new_enum = postgresql.ENUM('UPDATED', 'LOGIN_ERROR', 'UPDATING', 'OUTDATED', name='connectionstatus_new', create_type=True)
    new_enum.create(op.get_bind())
    
    # Alter column to use new enum type
    op.execute("ALTER TABLE open_finance_connection ALTER COLUMN status TYPE connectionstatus_new USING status::text::connectionstatus_new")
    
    # Drop old enum type
    op.execute("DROP TYPE connectionstatus")
    
    # Rename new enum type to old name
    op.execute("ALTER TYPE connectionstatus_new RENAME TO connectionstatus")


def downgrade() -> None:
    """Downgrade schema."""
    # Create old enum type
    old_enum = postgresql.ENUM('CONECTADO', 'ERRO_LOGIN', 'ATUALIZANDO', 'EXPIRADO', name='connectionstatus_old', create_type=True)
    old_enum.create(op.get_bind())
    
    # Alter column to use old enum type
    op.execute("ALTER TABLE open_finance_connection ALTER COLUMN status TYPE connectionstatus_old USING status::text::connectionstatus_old")
    
    # Drop current enum type
    op.execute("DROP TYPE connectionstatus")
    
    # Rename old enum type to current name
    op.execute("ALTER TYPE connectionstatus_old RENAME TO connectionstatus")
