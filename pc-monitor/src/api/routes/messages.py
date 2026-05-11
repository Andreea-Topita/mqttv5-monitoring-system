from typing import Optional

from fastapi import APIRouter, Query

from src.api.services.monitor_instance import monitor_service

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("")
def get_messages(topic: Optional[str] = None, after_id: Optional[int] = None):
    return {
        "success": True,
        "messages": monitor_service.get_messages(topic=topic, after_id=after_id)
    }


@router.get("/history")
def get_message_history(
    topic: Optional[str] = None,
    direction: Optional[str] = Query(default=None, pattern="^(INBOUND|OUTBOUND)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    return {
        "success": True,
        "data": monitor_service.get_message_history(
            topic=topic,
            direction=direction,
            page=page,
            page_size=page_size
        )
    }