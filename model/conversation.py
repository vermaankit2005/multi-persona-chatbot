import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func, text
from sqlalchemy.orm import mapped_column, Mapped

from model.base import Base


class Conversations(Base):
    __tablename__ = "conversations"

    __table_args__ = (
        Index("ix_conversations_user_id_updated_at", "user_id", text("updated_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    persona_key: Mapped[str] = mapped_column(ForeignKey("personas.key"))
    title: Mapped[str | None]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
