from schemas import BaseSchema
from pydantic import BaseModel, ConfigDict

class GradeSchema(BaseSchema):
    grade: int
    survey_id: int
    user_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "grade": 1,
                "survey_id": 1,
                "user_id": 1
            }
        },
    )