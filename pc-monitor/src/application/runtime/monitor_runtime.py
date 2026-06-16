import json
import threading
import time
from typing import Optional

from src.application.common.validators import (
    build_device_config_topic,
    build_device_topic,
    parse_device_topic
)
from src.domain.entities.live_message import LiveMessage

# starea live a aplicatiei : instanta client mqtt, daca pc e conectat sau nu la broker, daca periodic publish e activ sau nu, mesajele live
# topicurile la care clientul pc e abonat ( cheie topic, valoare qos )
class MonitorRuntime:
    def __init__(self):
        self.client = None
        self.connected = False
        self.periodic_publishing = False

        self.received_messages: list[LiveMessage] = []
        self.message_counter = 0

        self.subscriptions: dict[str, int] = {}
        self.devices: dict[str, dict] = {}

        # sa nu se modifice lista de mesaje sau dictionarul de subscriptii
        # in timp ce sunt accesate din threaduri diferite
        self.lock = threading.Lock()

        self.client_id = ""
        self.broker_address = ""
        self.broker_port = 1883

    # cand fac o conexiune noua, ca sa nu pastrez mesajele si subscriptions vechi
    def reset_live_state(self):
        with self.lock:
            self.received_messages = []
            self.message_counter = 0
            self.subscriptions = {}
            self.devices = {}
    
    # adaugare mesaj in lista de mesaje live
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

            # pastrare doar ultimele 200 de mesaje, ca sa nu creasca prea mult memoria folosita
            if len(self.received_messages) > 200:
                self.received_messages.pop(0)

            return item
        
    # pastrare doar ultimele 200 de mesaje, ca sa nu creasca prea mult memoria folosita
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

    def _topic_matches_filter(self, topic_filter: str, topic: str) -> bool:
        filter_parts = topic_filter.split("/")
        topic_parts = topic.split("/")

        for index, part in enumerate(filter_parts):
            if part == "#":
                return True

            if index >= len(topic_parts):
                return False

            if part == "+":
                continue

            if part != topic_parts[index]:
                return False

        return len(filter_parts) == len(topic_parts)

    def get_subscription_qos(self, topic: str) -> int:
        with self.lock:
            if topic in self.subscriptions:
                return self.subscriptions[topic]

            for topic_filter, qos in self.subscriptions.items():
                if self._topic_matches_filter(topic_filter, topic):
                    return qos

            return 0

    def set_subscription(self, topic: str, qos: int):
        with self.lock:
            self.subscriptions[topic] = qos

    def remove_subscription(self, topic: str):
        with self.lock:
            if topic in self.subscriptions:
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

    def _ensure_device_unlocked(self, client_id: str) -> dict:
        if client_id not in self.devices:
            self.devices[client_id] = {
                "client_id": client_id,
                "status": "unknown",
                "capabilities": [],
                "last_seen": None,
                "topics": {
                    "status": build_device_topic(client_id, "status"),
                    "temperatura": build_device_topic(client_id, "temperatura"),
                    "umiditate": build_device_topic(client_id, "umiditate"),
                    "config": build_device_config_topic(client_id)
                }
            }

        return self.devices[client_id]

    def register_device(
        self,
        client_id: str,
        status: Optional[str] = None,
        capabilities: Optional[list[str]] = None
    ):
        with self.lock:
            device = self._ensure_device_unlocked(client_id)
            device["last_seen"] = time.time()

            if status:
                device["status"] = status

            if capabilities:
                for capability in capabilities:
                    if capability not in device["capabilities"]:
                        device["capabilities"].append(capability)

    def update_device_from_message(
        self,
        topic: str,
        message: str,
        source_client_id: Optional[str] = None
    ):
        topic_info = parse_device_topic(topic)

        if topic_info is None:
            return

        client_id = topic_info["client_id"]
        category = topic_info["category"]

        with self.lock:
            device = self._ensure_device_unlocked(client_id)
            device["last_seen"] = time.time()

            if category == "status":
                status_value = message

                try:
                    payload = json.loads(message)

                    if isinstance(payload, dict):
                        status_value = payload.get("status", status_value)
                        capabilities = (
                            payload.get("capabilitati")
                            or payload.get("capabilities")
                            or []
                        )

                        for capability in capabilities:
                            if capability not in device["capabilities"]:
                                device["capabilities"].append(capability)
                except Exception:
                    pass

                device["status"] = status_value or "unknown"

            elif category in ("temperatura", "umiditate"):
                if category not in device["capabilities"]:
                    device["capabilities"].append(category)

                if device["status"] != "offline":
                    device["status"] = "online"

    def get_devices_copy(self) -> list[dict]:
        with self.lock:
            devices = [
                {
                    "client_id": device["client_id"],
                    "status": device["status"],
                    "capabilities": list(device["capabilities"]),
                    "last_seen": device["last_seen"],
                    "topics": dict(device["topics"])
                }
                for device in self.devices.values()
            ]

        return sorted(devices, key=lambda item: item["client_id"])