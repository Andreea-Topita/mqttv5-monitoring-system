from fastapi import APIRouter

from src.api.schemas.common import ActionResponse
from src.api.schemas.subscription import SubscribeRequest, UnsubscribeRequest
from src.application.services.service_container import monitor_service

router = APIRouter(prefix="/api/subscription", tags=["subscription"])


@router.post("/subscribe", response_model=ActionResponse)
def subscribe(payload: SubscribeRequest):
    monitor_service.subscribe(payload.topic, payload.qos)
    return ActionResponse(message=f"Subscribed to topic '{payload.topic}'.")


@router.post("/unsubscribe", response_model=ActionResponse)
def unsubscribe(payload: UnsubscribeRequest):
    monitor_service.unsubscribe(payload.topic)
    return ActionResponse(message=f"Unsubscribed from topic '{payload.topic}'.")