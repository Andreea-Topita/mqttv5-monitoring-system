from collections.abc import Sequence

from src.api.schemas.sensor_measurement import (
    SensorMeasurementResponse,
    SensorMeasurementsResponse
)
from src.domain.entities.sensor_measurement_record import SensorMeasurementRecord


def to_sensor_measurements_response(
    rows: Sequence[SensorMeasurementRecord]
) -> SensorMeasurementsResponse:
    items = [
        SensorMeasurementResponse.model_validate(row)
        for row in rows
    ]

    return SensorMeasurementsResponse(
        success=True,
        data=items
    )