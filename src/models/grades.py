from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Grades(Base):
    __tablename__ = "grades"
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True
    )
    grade: Mapped[int]
    survey_id: Mapped[int]
    user_id: Mapped[int]


