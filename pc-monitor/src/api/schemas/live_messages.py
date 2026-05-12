from pydantic import BaseModel


class LiveMessageItemResponse(BaseModel):
    id: int
    topic: str
    message: str
    timestamp: float


class LiveMessagesResponse(BaseModel):
    success: bool = True
    messages: list[LiveMessageItemResponse]