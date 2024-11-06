from typing import List, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.surveys import Survey
from schemas.surveys import SurveySchema


async def create_survey(
    db_session: AsyncSession,
    survey_data: SurveySchema,
    commit_and_refresh: bool = True,
) -> Survey:

    new_survey = Survey()
    new_survey.title = survey_data.title
    new_survey.body = survey_data.body
    new_survey.start_at = survey_data.start_at
    new_survey.finishes_at = survey_data.finishes_at

    db_session.add(new_survey)

    if commit_and_refresh:
        await db_session.commit()
        await db_session.refresh(new_survey)

    return new_survey


async def get_survey(db_session: AsyncSession, id: int) -> Survey | None:
    return (
        await db_session.scalars(select(Survey).where(Survey.id == id))
    ).first()


async def get_all_survey(db_session) -> List[Survey]:
    all_surveys = (await db_session.scalars(select(Survey))).all()
    return all_surveys
