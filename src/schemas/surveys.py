from schemas import BaseSchema
from pydantic import BaseModel, ConfigDict

class UserSchema(BaseSchema):
    title: str
    body: str
    starts_at: str
    finishes_At: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "title": "Title",
                "body": "Body"
            }
        },
    )