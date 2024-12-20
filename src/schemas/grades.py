from pydantic import BaseModel, ConfigDict

from schemas import BaseSchema


class GradeSchema(BaseSchema):
    grade: int
    survey_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {"grade": 1, "survey_id": 1, "user_id": 1}
        },
    )
