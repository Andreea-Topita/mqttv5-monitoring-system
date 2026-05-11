from fastapi import APIRouter

from src.api.schemas.subscription import SubscribeRequest, UnsubscribeRequest
from src.api.services.monitor_instance import monitor_service

router = APIRouter(prefix="/api/subscription", tags=["subscription"])


@router.post("/subscribe")
def subscribe(payload: SubscribeRequest):
    monitor_service.subscribe(payload.topic, payload.qos)
    return {
        "success": True,
        "message": f"Subscribed to topic '{payload.topic}'."
    }


@router.post("/unsubscribe")
def unsubscribe(payload: UnsubscribeRequest):
    monitor_service.unsubscribe(payload.topic)
    return {
        "success": True,
        "message": f"Unsubscribed from topic '{payload.topic}'."
    }