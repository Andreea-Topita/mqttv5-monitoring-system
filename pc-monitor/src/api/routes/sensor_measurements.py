from typing import Optional

from fastapi import APIRouter, Query

from src.api.mappers.sensor_measurements_mapper import to_sensor_measurements_response
from src.api.schemas.sensor_measurement import SensorMeasurementsResponse
from src.bootstrap.service_container import monitor_service


router = APIRouter(
    prefix="/api/sensor-measurements",
    tags=["sensor measurements"]
)


@router.get("", response_model=SensorMeasurementsResponse)
def get_sensor_measurements(
    measurement_name: Optional[str] = Query(default=None),
    topic: Optional[str] = Query(default=None),
    source_client_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500)
):
    rows = monitor_service.get_sensor_measurements(
        measurement_name=measurement_name,
        topic=topic,
        source_client_id=source_client_id,
        limit=limit
    )

    return to_sensor_measurements_response(rows)