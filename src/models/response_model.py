# schemas.py
import datetime

from pydantic import BaseModel


class SurveyCreateModel(BaseModel):
    title: str
    body: str
    start_at: datetime.datetime
    finishes_at: datetime.datetime


class SurveyResponseModel(BaseModel):
    id: int
    title: str
    body: str
    start_at: datetime.datetime
    finishes_at: datetime.datetime

    class Config:
        orm_mode = True
