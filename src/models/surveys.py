import datetime

from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True
    )
    title: Mapped[str]
    body: Mapped[str]
    start_at: Mapped[datetime.datetime]
    finishes_at: Mapped[datetime.datetime]