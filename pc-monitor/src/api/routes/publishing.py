from fastapi import APIRouter, HTTPException

from src.api.schemas.publish import PublishMetricRequest, PeriodicPublishRequest
from src.api.services.monitor_instance import monitor_service

router = APIRouter(prefix="/api/publishing", tags=["publishing"])


@router.post("/publish-metric")
def publish_metric(payload: PublishMetricRequest):
    try:
        message = monitor_service.publish_metric(payload.topic, payload.qos)
        return {
            "success": True,
            "message": "Metric published successfully.",
            "published_value": message
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start-periodic")
def start_periodic(payload: PeriodicPublishRequest):
    try:
        monitor_service.start_periodic_publish(
            topic=payload.topic,
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