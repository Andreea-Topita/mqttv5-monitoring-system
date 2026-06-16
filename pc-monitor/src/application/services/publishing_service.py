import json
import threading
import time

from src.application.common.persistence import persist_safely
from src.application.common.validators import (
    build_device_config_topic,
    validate_device_client_id,
    validate_interval,
    validate_qos,
    validate_topic
)
from src.application.runtime.monitor_runtime import MonitorRuntime
from src.domain.enums.mqtt_direction import MqttDirection
from src.domain.exceptions import (
    NotConnectedError,
    PeriodicPublishAlreadyRunningError,
    PeriodicPublishNotRunningError
)
from src.infrastructure.repositories.mqtt_message_repository import (
    MQTTMessageRepository
)


class PublishingService:
    def __init__(
        self,
        runtime: MonitorRuntime,
        mqtt_message_repository: MQTTMessageRepository
    ):
        self.runtime = runtime
        self.mqtt_message_repository = mqtt_message_repository

    def publish_message(self, topic: str, message: str, qos: int):
        if not self.runtime.client or not self.runtime.connected:
            raise NotConnectedError("Client is not connected to broker.")

        validate_topic(topic)
        validate_qos(qos)

        self.runtime.client.publish(topic, message, qos)

        persist_safely(
            "saving outbound mqtt message",
            self.mqtt_message_repository.add_message,
            topic=topic,
            payload=message,
            qos=qos,
            direction=MqttDirection.OUTBOUND.value,
            source_client_id=self.runtime.client_id
        )

    def configure_device(
        self,
        client_id: str,
        publish_qos: int,
        publish_interval: int,
        message_qos: int = 0
    ):
        if not self.runtime.client or not self.runtime.connected:
            raise NotConnectedError("Client is not connected to broker.")

        validate_device_client_id(client_id)
        validate_qos(publish_qos)
        validate_interval(publish_interval)
        validate_qos(message_qos)

        topic = build_device_config_topic(client_id)

        message = json.dumps(
            {
                "publish_qos": publish_qos,
                "publish_interval": publish_interval
            },
            separators=(",", ":")
        )

        self.publish_message(
            topic=topic,
            message=message,
            qos=message_qos
        )

        self.runtime.register_device(client_id)

        return {
            "topic": topic,
            "message": message
        }

    def start_periodic_publish(
        self,
        topic: str,
        message: str,
        qos: int,
        interval: int = 5
    ):
        if not self.runtime.connected:
            raise NotConnectedError("Client is not connected to broker.")

        validate_topic(topic)
        validate_qos(qos)
        validate_interval(interval)

        if self.runtime.periodic_publishing:
            raise PeriodicPublishAlreadyRunningError(
                "Periodic publishing is already running."
            )

        self.runtime.periodic_publishing = True

        threading.Thread(
            target=self._publish_periodically,
            args=(topic, message, qos, interval),
            daemon=True
        ).start()

    def _publish_periodically(
        self,
        topic: str,
        message: str,
        qos: int,
        interval: int
    ):
        while self.runtime.periodic_publishing:
            try:
                self.publish_message(topic, message, qos)
            except Exception as e:
                print(f"Periodic publish error: {e}")

            time.sleep(interval)

    def stop_periodic_publish(self):
        if not self.runtime.periodic_publishing:
            raise PeriodicPublishNotRunningError(
                "Periodic publishing is not running."
            )

        self.runtime.periodic_publishing = False