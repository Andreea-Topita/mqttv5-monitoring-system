from pydantic import BaseModel, Field, field_validator


class ConnectRequest(BaseModel):
    broker_address: str = Field(..., min_length=1, max_length=255)
    broker_port: int = Field(..., ge=1, le=65535)
    client_id: str = Field(..., min_length=1, max_length=100)
    username: str = ""
    password: str = ""
    last_will_topic: str = Field(..., min_length=1, max_length=255)
    last_will_message: str = Field(..., min_length=1)
    last_will_qos: int = Field(..., ge=0, le=2)
    last_will_retain: bool = False

    @field_validator("broker_address", "client_id", "last_will_topic", "last_will_message")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be empty.")
        return value