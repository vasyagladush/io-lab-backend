from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.grades import Grade
from schemas.grades import GradeSchema



async def add_grade(
    db_session: AsyncSession,
    grade_data: GradeSchema,
    commit_and_refresh: bool = True
) -> Grade:

    new_grade = Grade()
    new_grade.grade     = grade_data.grade
    new_grade.survey_id = grade_data.survey_id
    new_grade.user_id   = grade_data.user_id

    db_session.add(new_grade)

    if commit_and_refresh:
        await db_session.commit()
        await db_session.refresh(new_grade)

    return new_grade