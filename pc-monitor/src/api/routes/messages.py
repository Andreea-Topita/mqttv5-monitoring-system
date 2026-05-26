from typing import Optional

from fastapi import APIRouter, Query

from src.api.mappers.history_mapper import to_message_history_response
from src.api.mappers.live_messages_mapper import to_live_messages_response
from src.api.schemas.history import MessageHistoryResponse
from src.api.schemas.live_messages import LiveMessagesResponse
from src.bootstrap.service_container import monitor_service

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("", response_model=LiveMessagesResponse)
def get_messages(topic: Optional[str] = None, after_id: Optional[int] = None):
    rows = monitor_service.get_messages(topic=topic, after_id=after_id)
    return to_live_messages_response(rows)


@router.get("/history", response_model=MessageHistoryResponse)
def get_message_history(
    topic: Optional[str] = None,
    direction: Optional[str] = Query(default=None, pattern="^(INBOUND|OUTBOUND)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    rows, pagination = monitor_service.get_message_history(
        topic=topic,
        direction=direction,
        page=page,
        page_size=page_size
    )

    return to_message_history_response(rows, pagination)