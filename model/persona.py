from sqlalchemy.orm import Mapped, mapped_column

from model.base import Base


class Personas(Base):
    __tablename__ = "personas"

    key: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    system_prompt: Mapped[str]