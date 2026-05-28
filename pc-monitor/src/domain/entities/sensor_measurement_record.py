from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class SensorMeasurementRecord:
    id: int
    mqtt_message_id: Optional[int]
    topic: str
    source_client_id: Optional[str]
    base_name: Optional[str]
    measurement_name: str
    unit: str
    numeric_value: float
    measured_at: datetime
    created_at: datetime