from pydantic import BaseModel, Field, field_validator


class SubscribeRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255)
    qos: int = Field(..., ge=0, le=2)

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Topic must not be empty.")
        return value


class UnsubscribeRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255)

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Topic must not be empty.")
        return value