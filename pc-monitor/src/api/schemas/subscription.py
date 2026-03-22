from pydantic import BaseModel


class SubscribeRequest(BaseModel):
    topic: str
    qos: int


class UnsubscribeRequest(BaseModel):
    topic: str