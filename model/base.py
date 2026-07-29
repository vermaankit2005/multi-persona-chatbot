from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # docs/03-db-schema.md: text, never varchar. Without this, Mapped[str]
    # maps to String() and Postgres gets VARCHAR.
    type_annotation_map = {str: Text}
