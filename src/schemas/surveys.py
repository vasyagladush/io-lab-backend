from schemas import BaseSchema
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class SurveySchema(BaseSchema):
    title: str
    body: str
    starts_at: datetime
    finishes_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "title": "Title",
                "body": "Body"
            }
        },
    )

class SurveyPlusSchema(BaseSchema):
    title: str
    body: str
    starts_at: datetime
    finishes_at: datetime