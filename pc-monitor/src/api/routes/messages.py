from typing import Optional

from fastapi import APIRouter

from src.api.services.monitor_instance import monitor_service

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("")
def get_messages(topic: Optional[str] = None, after_id: Optional[int] = None):
    return {
        "success": True,
        "messages": monitor_service.get_messages(topic=topic, after_id=after_id)
    }