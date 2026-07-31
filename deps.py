from enum import Enum
from uuid import UUID

# Stand-in for a logged-in user until real auth lands. The matching row must
# exist in `users` (provider 'dev'), otherwise every conversation insert fails
# the foreign key.
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


def get_current_user_id() -> UUID:
    """The caller's user id.

    Routes depend on this instead of accepting a `user_id` parameter, so a
    client cannot ask for someone else's conversations. Swapping in real auth
    means decoding the token here — the routes stay unchanged.
    """
    return DEV_USER_ID
