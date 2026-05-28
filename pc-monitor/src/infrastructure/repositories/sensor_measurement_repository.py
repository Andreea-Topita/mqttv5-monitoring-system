from datetime import datetime
from typing import Optional

from sqlalchemy import select

from src.domain.entities.sensor_measurement_record import SensorMeasurementRecord
from src.infrastructure.database.session_manager import session_scope
from src.infrastructure.mappers.sensor_measurement_mapper import to_sensor_measurement_record
from src.infrastructure.models.sensor_measurement import SensorMeasurement


class SensorMeasurementRepository:
    def add_measurement(
        self,
        topic: str,
        source_client_id: Optional[str],
        base_name: Optional[str],
        measurement_name: str,
        unit: str,
        value: float,
        measured_at: datetime,
        mqtt_message_id: Optional[int] = None
    ) -> SensorMeasurementRecord:
        with session_scope() as db:
            item = SensorMeasurement(
                mqtt_message_id=mqtt_message_id,
                topic=topic,
                source_client_id=source_client_id,
                base_name=base_name,
                measurement_name=measurement_name,
                unit=unit,
                numeric_value=value,
                measured_at=measured_at
            )

            db.add(item)
            #trimite insert catre bd
            db.flush() 
            #citeste valorile generate de db, adica id si created_at
            db.refresh(item)

            #returneaza obiectul salvat ca un SensorMeasurementRecord
            return to_sensor_measurement_record(item)

    def get_measurements(
        self,
        measurement_name: Optional[str] = None,
        topic: Optional[str] = None,
        source_client_id: Optional[str] = None,
        limit: int = 50
    ) -> list[SensorMeasurementRecord]:
        limit = max(1, min(limit, 500))

        with session_scope() as db:
            filters = []

            if measurement_name:
                filters.append(SensorMeasurement.measurement_name == measurement_name)

            if topic:
                filters.append(SensorMeasurement.topic == topic)

            if source_client_id:
                filters.append(SensorMeasurement.source_client_id == source_client_id)

            stmt = select(SensorMeasurement)

            if filters:
                stmt = stmt.where(*filters)

            stmt = stmt.order_by(SensorMeasurement.measured_at.desc()).limit(limit)

            items = db.execute(stmt).scalars().all()

            records = [
                to_sensor_measurement_record(item)
                for item in items
            ]

            # pentru grafic vrem ordinea cronologica: de la vechi la nou
            records.reverse()

            return records