"""API request and response schemas.

These are the shapes FastAPI validates and serialises — they define the public
contract and drive the generated Swagger docs.

They are NOT database models. SQLAlchemy tables live separately (phase 2).
"""

from schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationOut,
)
from schemas.message import (
    DoneEvent,
    ErrorEvent,
    MessageCreate,
    MessageOut,
    MessageTurnOut,
    Role,
    TokenEvent,
)
from schemas.persona import PersonaOut

__all__ = [
    "PersonaOut",
    "ConversationCreate",
    "ConversationOut",
    "ConversationDetail",
    "MessageCreate",
    "MessageOut",
    "MessageTurnOut",
    "Role",
    "TokenEvent",
    "DoneEvent",
    "ErrorEvent",
]
