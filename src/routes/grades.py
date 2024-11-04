from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException

import services.grades as GradeService
from config import DBSessionDep, hash_helper
from models.surveys import Survey
from schemas.grades import GradeSchema

from services.auth import (
    AdminAccessCheckDep,
    AuthJWTTokenPayload,
    AuthJWTTokenValidatorDep,
    construct_auth_jwt,
)

router = APIRouter()



@router.post("/", status_code=201)
async def create_grade(
    db_session: DBSessionDep,
    auth_token_body: Annotated[AuthJWTTokenPayload, AuthJWTTokenValidatorDep],
    body: GradeSchema = Body(...),
) -> Survey:

    new_grade = await GradeService.create_survey(db_session, body)
    return new_grade
