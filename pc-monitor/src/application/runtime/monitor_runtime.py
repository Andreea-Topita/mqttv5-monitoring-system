import threading
import time
from typing import Optional

from src.domain.entities.live_message import LiveMessage


class MonitorRuntime:
    def __init__(self, on_message_callback=None):
        self.client = None
        self.connected = False
        self.periodic_publishing = False
        self.external_on_message_callback = on_message_callback

        self.received_messages: list[LiveMessage] = []
        self.message_counter = 0

        self.subscriptions: dict[str, int] = {}

        self.lock = threading.Lock()

        self.client_id = ""
        self.broker_address = ""
        self.broker_port = 1883

    def reset_runtime_messages(self):
        with self.lock:
            self.received_messages = []
            self.message_counter = 0
            self.subscriptions = {}

    def add_live_message(self, topic: str, message: str) -> LiveMessage:
        with self.lock:
            self.message_counter += 1

            item = LiveMessage(
                id=self.message_counter,
                topic=topic,
                message=message,
                timestamp=time.time()
            )

            self.received_messages.append(item)

            if len(self.received_messages) > 100:
                self.received_messages.pop(0)

            return item

    def get_live_messages(
        self,
        topic: Optional[str] = None,
        after_id: Optional[int] = None
    ) -> list[LiveMessage]:
        with self.lock:
            messages = list(self.received_messages)

        if topic:
            messages = [
                message for message in messages
                if message.topic == topic
            ]

        if after_id is not None:
            messages = [
                message for message in messages
                if message.id > after_id
            ]

        return messages

    def get_subscription_qos(self, topic: str) -> int:
        with self.lock:
            return self.subscriptions.get(topic, 0)

    def set_subscription(self, topic: str, qos: int):
        with self.lock:
            self.subscriptions[topic] = qos

    def remove_subscription(self, topic: str):
        with self.lock:
            del self.subscriptions[topic]

    def has_subscription(self, topic: str) -> bool:
        with self.lock:
            return topic in self.subscriptions

    def get_subscriptions_copy(self) -> dict[str, int]:
        with self.lock:
            return dict(self.subscriptions)

    def clear_subscriptions(self):
        with self.lock:
            self.subscriptions.clear()