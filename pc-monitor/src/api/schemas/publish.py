from pydantic import BaseModel


class PublishMetricRequest(BaseModel):
    topic: str
    qos: int


class PeriodicPublishRequest(BaseModel):
    topic: str
    qos: int
    interval: int = 5