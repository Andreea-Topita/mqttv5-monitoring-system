import json
from datetime import datetime, timezone
from typing import Optional

from src.application.common.validators import (
    is_sensor_topic,
    is_valid_sensor_measurement
)
from src.infrastructure.repositories.sensor_measurement_repository import (
    SensorMeasurementRepository
)

# serviciul care se ocupa de masuratorile senzorilor, primeste mesajele mqtt de la MessageService, le decodeaza si le salveaza in baza de date
class SensorMeasurementService:
    def __init__(
        self,
        sensor_measurement_repository: SensorMeasurementRepository
    ):
        self.sensor_measurement_repository = sensor_measurement_repository

    def handle_possible_sensor_message(
        self,
        topic: str,
        payload: str,
        source_client_id: Optional[str] = None,
        mqtt_message_id: Optional[int] = None
    ) -> None:
        # salvam numeric doar mesajele de pe topicurile de senzori, statusul online/offline ramane doar in mqtt_messages
        # daca topicul nu este de senzor, nu facem nimic
        if not is_sensor_topic(topic):
            return

        # daca payload-ul nu este un json valid, nu facem nimic
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return

        # payload-ul SenML este o lista de inregistrari
        # daca nu e o lista, nu facem nimic
        if not isinstance(data, list):
            return

        for record in data:
            if not isinstance(record, dict):
                continue
            
            # extragerea campurilor din inregistrarea SenML, daca lipseste vreunul, trecem la urmatoarea inregistrare
            base_name = record.get("bn")
            measurement_name = record.get("n")
            unit = record.get("u")
            value = record.get("v")
            timestamp = record.get("t")

            # validare daca lipseste vreun camp, trecem la urmatoarea inregistrare
            if measurement_name is None or unit is None or value is None or timestamp is None:
                continue

            try:
                value = float(value)
                timestamp = float(timestamp)
            except (TypeError, ValueError):
                continue

            if not is_valid_sensor_measurement(topic, measurement_name, unit, value):
                continue

            # daca primesc t invalid, nu vreau sa salvez inregistrarea
            # dar nici sa opresc procesarea celorlalte inregistrari valide din payload, de aceea prind exceptia doar pentru conversia timestamp-ului
            try:
                measured_at = datetime.fromtimestamp(
                    timestamp,
                    timezone.utc
                ).replace(tzinfo=None)
            except (OverflowError, OSError, ValueError):
                continue
            # transform unix timestamp in datetime UTC, pentru a fi compatibil cu campul measured_at din baza de date

            self.sensor_measurement_repository.add_measurement(
                topic=topic,
                source_client_id=source_client_id,
                base_name=base_name,
                measurement_name=measurement_name,
                unit=unit,
                value=value,
                measured_at=measured_at,
                mqtt_message_id=mqtt_message_id
            )
    
    def get_measurements(
        self,
        measurement_name: Optional[str] = None,
        topic: Optional[str] = None,
        source_client_id: Optional[str] = None,
        limit: int = 50
    ):
        return self.sensor_measurement_repository.get_measurements(
            measurement_name=measurement_name,
            topic=topic,
            source_client_id=source_client_id,
            limit=limit
        )