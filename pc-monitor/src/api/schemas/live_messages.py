from pydantic import BaseModel, ConfigDict


#forma trimisa catre frontend 
class LiveMessageItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    message: str
    timestamp: float


class LiveMessagesResponse(BaseModel):
    success: bool = True
    messages: list[LiveMessageItemResponse]