"""SQLAlchemy ORM models.

Every model must be imported here. Importing a model registers its table on
``Base.metadata``, which is what Alembic reads when generating migrations.
A model missing from this list is invisible to ``alembic --autogenerate``.
"""

from model.base import Base
from model.conversation import Conversations
from model.message import Messages
from model.persona import Personas
from model.user import Users

__all__ = [
    "Base",
    "Personas",
    "Users",
    "Conversations",
    "Messages",
]
