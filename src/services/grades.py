from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.grades import Grade
from schemas.grades import GradeSchema


async def add_grade(
    db_session: AsyncSession,
    grade_data: GradeSchema,
    commit_and_refresh: bool = True,
) -> Grade:

    new_grade = Grade()
    new_grade.grade = grade_data.grade
    new_grade.survey_id = grade_data.survey_id
    new_grade.user_id = grade_data.user_id

    db_session.add(new_grade)

    if commit_and_refresh:
        await db_session.commit()
        await db_session.refresh(new_grade)

    return new_grade


async def get_grade_for_survey(
    db_session: AsyncSession, user_id: int, survey_id: int
) -> Grade:
    return (
        await db_session.scalars(
            select(Grade).where(
                Grade.user_id == user_id and Grade.survey_id == survey_id
            )
        )
    ).first()


async def get_grades_by_survey(
    db_session: AsyncSession, survey_id: int
) -> Sequence[Grade]:
    return (
        await db_session.scalars(
            select(Grade).where(Grade.survey_id == survey_id)
        )
    ).all()
