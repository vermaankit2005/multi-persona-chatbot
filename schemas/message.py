from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

Role = Literal["user", "assistant", "system"]

# Whitespace is stripped before the length checks run, so "   " is rejected
# as empty rather than sneaking through as a 3-character message.
MessageContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
]


class MessageCreate(BaseModel):
    """Body of POST /conversations/{id}/messages."""

    content: MessageContent


class MessageOut(BaseModel):
    """A single stored message."""

    # Routes build this straight from ORM rows, so reading attributes off the
    # object has to be allowed — FastAPI only does that for `response_model`.
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Role
    content: str
    created_at: datetime


class MessageTurnOut(BaseModel):
    """Response of POST /conversations/{id}/messages.

    Both rows are returned so the client can render the whole turn without a
    second request.
    """

    user_message: MessageOut
    assistant_message: MessageOut


# --- Phase 4: SSE event payloads -------------------------------------------
# These are the `data:` bodies of the server-sent events, not HTTP responses.


class TokenEvent(BaseModel):
    """event: token — one chunk of the reply as it is generated."""

    text: str


class DoneEvent(BaseModel):
    """event: done — the real database IDs, sent once the stream completes.

    The client attaches these to the bubbles it has already rendered.
    """

    user_message_id: int
    assistant_message_id: int


class ErrorEvent(BaseModel):
    """event: error — a failure after streaming has already begun.

    The status code is locked in once the first byte is sent, so a mid-stream
    failure cannot be a 502.
    """

    detail: str
