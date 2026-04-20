from pydantic import BaseModel


class PublishMessageRequest(BaseModel):
    topic: str
    message: str
    qos: int


class PeriodicPublishRequest(BaseModel):
    topic: str
    message: str
    qos: int
    interval: int = 5