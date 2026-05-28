from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SensorMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mqtt_message_id: Optional[int] = None
    topic: str
    source_client_id: Optional[str] = None
    base_name: Optional[str] = None
    measurement_name: str
    unit: str
    numeric_value: float
    measured_at: datetime
    created_at: datetime


class SensorMeasurementsResponse(BaseModel):
    success: bool = True
    data: list[SensorMeasurementResponse]