from sqlalchemy.exc import IntegrityError

from model import Users


def db_get_or_create_user(provider: str, provider_user_id: str, email: str | None, db_session) -> Users:
    """The local row for an identity provider's user, created on first sight.

    `provider_user_id` is the id the provider owns (Clerk's looks like
    `user_2abc123XYZ`). It can't be a foreign key target, so every provider
    user gets a mirror row here whose UUID `conversations.user_id` points at.
    """
    user = __db_get_user_by_provider(provider, provider_user_id, db_session)
    if user:
        return user

    user = Users(provider=provider, provider_user_id=provider_user_id, email=email)
    try:
        db_session.add(user)
        db_session.commit()
    except IntegrityError:
        # Two requests from the same brand-new user can reach the insert at the
        # same time. The unique constraint on (provider, provider_user_id) means
        # one of them loses — read back the row the winner wrote.
        db_session.rollback()
        return __db_get_user_by_provider(provider, provider_user_id, db_session)

    db_session.refresh(user)
    return user


def __db_get_user_by_provider(provider: str, provider_user_id: str, db_session) -> Users | None:
    return (db_session.query(Users)
            .filter(Users.provider == provider, Users.provider_user_id == provider_user_id)
            .first())
