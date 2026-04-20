from fastapi import APIRouter, HTTPException

from src.api.schemas.publish import PublishMessageRequest, PeriodicPublishRequest
from src.api.services.monitor_instance import monitor_service

router = APIRouter(prefix="/api/publishing", tags=["publishing"])


@router.post("/publish-message")
def publish_message(payload: PublishMessageRequest):
    try:
        monitor_service.publish_message(
            topic=payload.topic,
            message=payload.message,
            qos=payload.qos
        )
        return {
            "success": True,
            "message": "Message published successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start-periodic")
def start_periodic(payload: PeriodicPublishRequest):
    try:
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop-periodic")
def stop_periodic():
    try:
        monitor_service.stop_periodic_publish()
        return {
            "success": True,
            "message": "Periodic publish stopped."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))