from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.surveys import Surveys
from schemas.surveys import UserSignUpSchema


async def create_survey(
    db_session: AsyncSession,
    survey_data: UserSignUpSchema, #TODO
    commit_and_refresh: bool = True,
) -> Surveys:

    new_survey = Surveys()
    new_survey.title = survey_data.title
    new_survey.body = survey_data.body
    new_survey.start_at = survey_data.start_at
    new_survey.finishes_at = survey_data.finishes_at

    db_session.add(new_survey)

    if commit_and_refresh:
        await db_session.commit()
        await db_session.refresh(new_survey)

    return new_survey