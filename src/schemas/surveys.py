from datetime import datetime

from pydantic import ConfigDict

from schemas import BaseSchema


class SurveySchema(BaseSchema):
    title: str
    body: str
    start_at: datetime
    finishes_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"title": "Title", "body": "Body"}},
    )


class SurveyPlusSchema(SurveySchema):
    id: int
