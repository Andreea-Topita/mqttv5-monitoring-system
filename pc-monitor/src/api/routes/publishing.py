from fastapi import APIRouter

from src.api.schemas.common import ActionResponse
from src.api.schemas.publish import (
    DeviceConfigRequest,
    PeriodicPublishRequest,
    PublishMessageRequest
)
from src.bootstrap.service_container import monitor_service

router = APIRouter(prefix="/api/publishing", tags=["publishing"])


@router.post("/publish-message", response_model=ActionResponse)
def publish_message(payload: PublishMessageRequest):
    monitor_service.publish_message(
        topic=payload.topic,
        message=payload.message,
        qos=payload.qos
    )
    return ActionResponse(message="Message published successfully.")


@router.post("/device-config", response_model=ActionResponse)
def configure_device(payload: DeviceConfigRequest):
    result = monitor_service.configure_device(
        client_id=payload.client_id,
        publish_qos=payload.publish_qos,
        publish_interval=payload.publish_interval,
        message_qos=payload.message_qos
    )

    return ActionResponse(
        message=(
            "Device configuration sent to "
            f"{result['topic']}: {result['message']}"
        )
    )


@router.post("/start-periodic", response_model=ActionResponse)
def start_periodic(payload: PeriodicPublishRequest):
    monitor_service.start_periodic_publish(
        topic=payload.topic,
        message=payload.message,
        qos=payload.qos,
        interval=payload.interval
    )
    return ActionResponse(message="Periodic publish started.")


@router.post("/stop-periodic", response_model=ActionResponse)
def stop_periodic():
    monitor_service.stop_periodic_publish()
    return ActionResponse(message="Periodic publish stopped.")