from fastapi import APIRouter

from src.api.schemas.publish import PublishMessageRequest, PeriodicPublishRequest
from src.api.services.monitor_instance import monitor_service

router = APIRouter(prefix="/api/publishing", tags=["publishing"])


@router.post("/publish-message")
def publish_message(payload: PublishMessageRequest):
    monitor_service.publish_message(
        topic=payload.topic,
        message=payload.message,
        qos=payload.qos
    )
    return {
        "success": True,
        "message": "Message published successfully."
    }


@router.post("/start-periodic")
def start_periodic(payload: PeriodicPublishRequest):
    monitor_service.start_periodic_publish(
        topic=payload.topic,
        message=payload.message,
        qos=payload.qos,
        interval=payload.interval
    )
    return {
        "success": True,
        "message": "Periodic publish started."
    }


@router.post("/stop-periodic")
def stop_periodic():
    monitor_service.stop_periodic_publish()
    return {
        "success": True,
        "message": "Periodic publish stopped."
    }