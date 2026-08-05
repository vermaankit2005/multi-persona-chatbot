"""allow clerk provider in users

Revision ID: b7c41e0a9d32
Revises: 8d5ca097cdbb
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c41e0a9d32'
down_revision: Union[str, Sequence[str], None] = '8d5ca097cdbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Real logins come from Clerk, so 'clerk' has to pass the provider check.
    op.drop_constraint('check_provider', 'users', type_='check')
    op.create_check_constraint(
        'check_provider', 'users', "provider IN ('clerk', 'google', 'github', 'dev')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Existing clerk rows would fail the narrower constraint, so drop them
    # first. Their conversations and messages go too, via ON DELETE CASCADE.
    op.execute("DELETE FROM users WHERE provider = 'clerk'")
    op.drop_constraint('check_provider', 'users', type_='check')
    op.create_check_constraint(
        'check_provider', 'users', "provider IN ('google', 'github', 'dev')"
    )
