"""allow system role in messages

Revision ID: 8d5ca097cdbb
Revises: 1d0eab10f03b
Create Date: 2026-07-31 22:02:27.872075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d5ca097cdbb'
down_revision: Union[str, Sequence[str], None] = '1d0eab10f03b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The persona's system prompt is stored as the first row of every
    # conversation, so 'system' has to pass the role check.
    op.drop_constraint('check_role', 'messages', type_='check')
    op.create_check_constraint(
        'check_role', 'messages', "role IN ('user', 'assistant', 'system')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Existing system rows would fail the narrower constraint, so drop them
    # before putting it back.
    op.execute("DELETE FROM messages WHERE role = 'system'")
    op.drop_constraint('check_role', 'messages', type_='check')
    op.create_check_constraint(
        'check_role', 'messages', "role IN ('user', 'assistant')"
    )
