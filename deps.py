from enum import Enum
from uuid import UUID

import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from config import settings
from db import get_db_session
from repository.user_repo import db_get_or_create_user

# Every real login goes through Clerk, so every `users` row created here carries
# this provider. See the check constraint in model/user.py.
CLERK_PROVIDER = "clerk"

# One client for the process. It caches Clerk's public signing keys, so
# verifying a token is a local signature check, not a network call per request.
clerk = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)

# Declared only so Swagger shows an "Authorize" button and sends the header.
# auto_error=False means a request without it still reaches Clerk, which also
# accepts the __session cookie a browser would send instead.
bearer_scheme = HTTPBearer(auto_error=False)


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


def get_current_user_id(request: Request,
                        _credentials=Depends(bearer_scheme),
                        db: Session = Depends(get_db_session)) -> UUID:
    """The caller's user id, proven by their Clerk token.

    Routes depend on this instead of accepting a `user_id` parameter, so a
    client cannot ask for someone else's conversations. The token is the only
    source of identity — nothing in the body or query string is trusted.
    """
    request_state = clerk.authenticate_request(
        # Clerk's SDK reads an httpx request. Only the headers matter: it looks
        # for `Authorization: Bearer <token>` first, then the `__session` cookie.
        httpx.Request(request.method, str(request.url), headers=request.headers.raw),
        AuthenticateRequestOptions(authorized_parties=settings.CLERK_AUTHORIZED_PARTIES),
    )

    if not request_state.is_signed_in:
        raise HTTPException(status_code=401, detail=f"Not signed in: {request_state.reason}")

    # `sub` is Clerk's id for the person, stable for the life of their account.
    clerk_user_id = request_state.payload["sub"]
    # Clerk's default session token carries no email. It stays NULL unless you
    # add an `email` claim under Sessions > Customize session token.
    email = request_state.payload.get("email")

    user = db_get_or_create_user(CLERK_PROVIDER, clerk_user_id, email, db)
    return user.id
