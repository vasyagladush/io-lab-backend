import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Grade(Base):
    __tablename__ = "grades"
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True
    )
    grade: Mapped[int]
    survey_id: Mapped[int]
    user_id: Mapped[int]
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
