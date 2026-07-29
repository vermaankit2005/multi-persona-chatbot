import uuid

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from model.base import Base


class Users(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("provider IN ('google', 'github', 'dev')", name="check_provider"),
        UniqueConstraint("provider", "provider_user_id", name="uq_users_provider_provider_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider: Mapped[str]
    provider_user_id: Mapped[str]
    email: Mapped[str | None]