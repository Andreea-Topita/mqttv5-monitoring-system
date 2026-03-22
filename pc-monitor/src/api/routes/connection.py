from fastapi import APIRouter, HTTPException

from src.api.schemas.connection import ConnectRequest
from src.api.services.monitor_instance import monitor_service

router = APIRouter(prefix="/api/connection", tags=["connection"])


@router.post("/connect")
def connect(payload: ConnectRequest):
    try:
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
        return {
            "success": True,
            "message": "Connected successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disconnect")
def disconnect():
    try:
        monitor_service.disconnect()
        return {
            "success": True,
            "message": "Disconnected successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
def get_status():
    return monitor_service.get_status()