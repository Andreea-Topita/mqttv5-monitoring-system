from typing import Optional

from src.application.common.pagination import build_pagination
from src.application.common.persistence import persist_safely
from src.application.runtime.monitor_runtime import MonitorRuntime
from src.application.services.sensor_measurement_service import SensorMeasurementService
from src.domain.enums.mqtt_direction import MqttDirection
from src.infrastructure.repositories.mqtt_message_repository import MQTTMessageRepository


class MessageService:
    def __init__(
        self,
        runtime: MonitorRuntime,
        mqtt_message_repository: MQTTMessageRepository,
        sensor_measurement_service: SensorMeasurementService
    ):
        self.runtime = runtime
        self.mqtt_message_repository = mqtt_message_repository
        self.sensor_measurement_service = sensor_measurement_service

    def handle_incoming_message(
        self,
        topic: str,
        message: str,
        source_client_id: Optional[str] = None
    ):
        self.runtime.add_live_message(topic, message)
        
        self.runtime.update_device_from_message(
            topic=topic,
            message=message,
            source_client_id=source_client_id
        )

        current_qos = self.runtime.get_subscription_qos(topic)

        saved_message = persist_safely(
            "saving inbound mqtt message",
            self.mqtt_message_repository.add_message,
            topic=topic,
            payload=message,
            qos=current_qos,
            direction=MqttDirection.INBOUND.value,
            source_client_id=source_client_id
        )

        mqtt_message_id = saved_message.id if saved_message else None

        persist_safely(
            "saving numeric sensor measurement",
            self.sensor_measurement_service.handle_possible_sensor_message,
            topic=topic,
            payload=message,
            source_client_id=source_client_id,
            mqtt_message_id=mqtt_message_id
        )

    def get_live_messages(
        self,
        topic: Optional[str] = None,
        after_id: Optional[int] = None
    ):
        return self.runtime.get_live_messages(
            topic=topic,
            after_id=after_id
        )

    def get_message_history(
        self,
        topic: Optional[str] = None,
        direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ):
        rows, total_items = self.mqtt_message_repository.get_messages_paginated(
            topic=topic,
            direction=direction,
            page=page,
            page_size=page_size
        )

        pagination = build_pagination(page, page_size, total_items)

        return rows, pagination