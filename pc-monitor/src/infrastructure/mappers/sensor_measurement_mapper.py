from src.domain.entities.sensor_measurement_record import SensorMeasurementRecord
from src.infrastructure.models.sensor_measurement import SensorMeasurement


def to_sensor_measurement_record(item: SensorMeasurement) -> SensorMeasurementRecord:
    return SensorMeasurementRecord(
        id=item.id,
        mqtt_message_id=item.mqtt_message_id,
        topic=item.topic,
        source_client_id=item.source_client_id,
        base_name=item.base_name,
        measurement_name=item.measurement_name,
        unit=item.unit,
        numeric_value=item.numeric_value,
        measured_at=item.measured_at,
        created_at=item.created_at
    )