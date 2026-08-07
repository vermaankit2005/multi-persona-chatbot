from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, StringConstraints

from schemas.message import MessageOut

class ConversationCreate(BaseModel):
    """Body of POST /conversations.

    A typo like "grumy_pirate" is still a valid string, so the service layer
    checks the persona exists and returns 404 if it does not.
    """
    persona_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class ConversationOut(BaseModel):
    """A conversation without its messages.

    Used for both the POST /conversations response and each row of the
    sidebar list — they are the same shape.
    """

    id: UUID
    persona_key: str
    title: str | None
    updated_at: datetime


class ConversationDetail(ConversationOut):
    """Response of GET /conversations/{id} — everything the thread screen needs.

    all `messages`, oldest first: the order they render in.
    """

    messages: list[MessageOut]

class ConversationDelete(BaseModel):
    """Response of DELETE /conversations/{id} — confirmation of deletion."""
    id: UUID
