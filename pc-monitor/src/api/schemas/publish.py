from pydantic import BaseModel, Field, field_validator


class PublishMessageRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    qos: int = Field(..., ge=0, le=2)

    @field_validator("topic", "message")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be empty.")
        return value


class PeriodicPublishRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    qos: int = Field(..., ge=0, le=2)
    interval: int = Field(default=5, gt=0)

    @field_validator("topic", "message")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be empty.")
        return value