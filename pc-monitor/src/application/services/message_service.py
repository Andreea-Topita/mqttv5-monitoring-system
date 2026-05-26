from typing import Optional

from src.application.common.pagination import build_pagination
from src.application.common.persistence import persist_safely
from src.application.runtime.monitor_runtime import MonitorRuntime
from src.domain.enums.mqtt_direction import MqttDirection
from src.infrastructure.repositories.mqtt_message_repository import MQTTMessageRepository


class MessageService:
    def __init__(
        self,
        runtime: MonitorRuntime,
        mqtt_message_repository: MQTTMessageRepository
    ):
        self.runtime = runtime
        self.mqtt_message_repository = mqtt_message_repository

    def handle_incoming_message(
        self,
        topic: str,
        message: str,
        source_client_id: Optional[str] = None
    ):
        self.runtime.add_live_message(topic, message)

        current_qos = self.runtime.get_subscription_qos(topic)

        persist_safely(
            "saving inbound mqtt message",
            self.mqtt_message_repository.add_message,
            topic=topic,
            payload=message,
            qos=current_qos,
            direction=MqttDirection.INBOUND.value,
            source_client_id=source_client_id
        )

        if self.runtime.external_on_message_callback:
            self.runtime.external_on_message_callback(
                topic,
                message,
                source_client_id
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