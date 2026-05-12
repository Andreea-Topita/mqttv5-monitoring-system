from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MessageHistoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    payload: str
    qos: int
    direction: str
    source_client_id: str | None = None
    created_at: datetime | None = None


class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class MessageHistoryDataResponse(BaseModel):
    items: list[MessageHistoryItemResponse]
    pagination: PaginationResponse


class MessageHistoryResponse(BaseModel):
    success: bool = True
    data: MessageHistoryDataResponse