from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from model.message import MessageOut

PersonaKey = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
]


class ConversationCreate(BaseModel):
    """Body of POST /conversations.

    A typo like "grumy_pirate" is still a valid string, so the service layer
    checks the persona exists and returns 404 if it does not.
    """

    model_config = ConfigDict(
        json_schema_extra={"example": {"persona_key": "grumpy_pirate"}}
    )

    persona_key: PersonaKey


class ConversationOut(BaseModel):
    """A conversation without its messages.

    Used for both the POST /conversations response and each row of the
    sidebar list — they are the same shape.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    persona_key: str
    title: str | None
    updated_at: datetime


class ConversationDetail(ConversationOut):
    """Response of GET /conversations/{id} — everything the thread screen needs.

    `messages` is the last 50, oldest first: the order they render in.
    """

    messages: list[MessageOut]
