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

class DeviceConfigRequest(BaseModel):
    client_id: str = Field(..., min_length=1, max_length=80)
    publish_qos: int = Field(..., ge=0, le=2)
    publish_interval: int = Field(..., gt=0)
    message_qos: int = Field(default=0, ge=0, le=2)

    @field_validator("client_id")
    @classmethod
    def client_id_must_be_valid(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Client ID must not be empty.")

        for char in value:
            if not (char.isalnum() or char in ["_", "-"]):
                raise ValueError("Client ID may contain only letters, digits, _ and -.")

        return value