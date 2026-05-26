from fastapi import APIRouter

from src.api.schemas.common import ActionResponse
from src.api.schemas.connection import ConnectRequest
from src.api.schemas.status import MonitorStatusResponse
from src.bootstrap.service_container import monitor_service

router = APIRouter(prefix="/api/connection", tags=["connection"])


@router.post("/connect", response_model=ActionResponse)
def connect(payload: ConnectRequest):
    monitor_service.connect(
        broker_address=payload.broker_address,
        broker_port=payload.broker_port,
        client_id=payload.client_id,
        username=payload.username,
        password=payload.password,
        last_will_topic=payload.last_will_topic,
        last_will_message=payload.last_will_message,
        last_will_qos=payload.last_will_qos,
        last_will_retain=payload.last_will_retain,
    )
    return ActionResponse(message="Connected successfully.")


@router.post("/disconnect", response_model=ActionResponse)
def disconnect():
    monitor_service.disconnect()
    return ActionResponse(message="Disconnected successfully.")


@router.get("/status", response_model=MonitorStatusResponse)
def get_status():
    return MonitorStatusResponse(**monitor_service.get_status())