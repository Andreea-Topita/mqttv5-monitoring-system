import threading
import time
from typing import Optional

from src.client.mqtt_client import MQTTClient
from src.repositories.connection_event_repository import ConnectionEventRepository
from src.repositories.subscription_event_repository import SubscriptionEventRepository
from src.repositories.mqtt_message_repository import MQTTMessageRepository


class MonitorService:
    def __init__(
        self,
        on_message_callback=None,
        connection_event_repository: Optional[ConnectionEventRepository] = None,
        subscription_event_repository: Optional[SubscriptionEventRepository] = None,
        mqtt_message_repository: Optional[MQTTMessageRepository] = None
    ):
        self.client = None
        self.connected = False
        self.periodic_publishing = False
        self.external_on_message_callback = on_message_callback

        # mesaje primite de la broker, tinute in memorie pentru UI live
        self.received_messages = []
        self.message_counter = 0

        # topic -> qos
        self.subscriptions = {}

        self.lock = threading.Lock()

        # date despre conexiunea curenta
        self.client_id = ""
        self.broker_address = ""
        self.broker_port = 1883

        # repositories
        self.connection_event_repository = connection_event_repository or ConnectionEventRepository()
        self.subscription_event_repository = subscription_event_repository or SubscriptionEventRepository()
        self.mqtt_message_repository = mqtt_message_repository or MQTTMessageRepository()

    def _persist_safely(self, action_name: str, callback, *args, **kwargs):
        try:
            callback(*args, **kwargs)
        except Exception as e:
            print(f"Persistence error during {action_name}: {e}")

    def _append_in_memory_message(self, topic: str, message: str):
        with self.lock:
            self.message_counter += 1
            self.received_messages.append({
                "id": self.message_counter,
                "topic": topic,
                "message": message,
                "timestamp": time.time()
            })

            if len(self.received_messages) > 100:
                self.received_messages.pop(0)

    def _handle_incoming_message(self, topic: str, message: str):
        self._append_in_memory_message(topic, message)

        with self.lock:
            current_qos = self.subscriptions.get(topic, 0)

        self._persist_safely(
            "saving inbound mqtt message",
            self.mqtt_message_repository.add_message,
            topic=topic,
            payload=message,
            qos=current_qos,
            direction="INBOUND",
            source_client_id=None
        )

        if self.external_on_message_callback:
            self.external_on_message_callback(topic, message)

    def connect(
        self,
        broker_address: str,
        broker_port: int,
        client_id: str,
        username: str,
        password: str,
        last_will_topic: str,
        last_will_message: str,
        last_will_qos: int,
        last_will_retain: bool = False,
    ):
        with self.lock:
            self.received_messages = []
            self.message_counter = 0
            self.subscriptions = {}

        self.client_id = client_id
        self.broker_address = broker_address
        self.broker_port = broker_port

        self.client = MQTTClient(
            client_id=client_id,
            on_message_callback=self._handle_incoming_message
        )

        self.client.will_set(
            last_will_topic,
            last_will_message,
            qos=last_will_qos,
            retain=last_will_retain
        )
        self.client.username_pw_set(username, password)
        self.client.conectare_broker(broker_address, broker_port)

        self.connected = True

        self._persist_safely(
            "saving connect event",
            self.connection_event_repository.add_event,
            client_id=client_id,
            broker_address=broker_address,
            broker_port=broker_port,
            event_type="CONNECT"
        )

    def disconnect(self):
        if self.client and self.connected:
            try:
                self.client.disconnect()
            finally:
                self._persist_safely(
                    "saving disconnect event",
                    self.connection_event_repository.add_event,
                    client_id=self.client_id,
                    broker_address=self.broker_address,
                    broker_port=self.broker_port,
                    event_type="DISCONNECT"
                )

            self.connected = False
            self.periodic_publishing = False
            self.client = None

        with self.lock:
            self.subscriptions.clear()

    def publish_message(self, topic: str, message: str, qos: int):
        if not self.client or not self.connected:
            raise RuntimeError("Not connected to broker.")

        self.client.publish(topic, message, qos)

        self._persist_safely(
            "saving outbound mqtt message",
            self.mqtt_message_repository.add_message,
            topic=topic,
            payload=message,
            qos=qos,
            direction="OUTBOUND",
            source_client_id=self.client_id
        )

    def subscribe(self, topic: str, qos: int):
        if not self.client or not self.connected:
            raise RuntimeError("Not connected to broker.")

        self.client.subscribe(topic, qos)

        with self.lock:
            self.subscriptions[topic] = qos

        self._persist_safely(
            "saving subscribe event",
            self.subscription_event_repository.add_event,
            topic=topic,
            qos=qos,
            action="SUBSCRIBE"
        )

    def unsubscribe(self, topic: str):
        if not self.client or not self.connected:
            raise RuntimeError("Not connected to broker.")

        old_qos = 0
        with self.lock:
            if topic in self.subscriptions:
                old_qos = self.subscriptions[topic]

        self.client.unsubscribe(topic)

        with self.lock:
            if topic in self.subscriptions:
                del self.subscriptions[topic]

        self._persist_safely(
            "saving unsubscribe event",
            self.subscription_event_repository.add_event,
            topic=topic,
            qos=old_qos,
            action="UNSUBSCRIBE"
        )

    def start_periodic_publish(self, topic: str, message: str, qos: int, interval: int = 5):
        if not self.connected:
            raise RuntimeError("Not connected to broker.")

        if self.periodic_publishing:
            raise RuntimeError("Periodic publishing is already running.")

        self.periodic_publishing = True
        threading.Thread(
            target=self._publish_periodically,
            args=(topic, message, qos, interval),
            daemon=True
        ).start()

    def _publish_periodically(self, topic: str, message: str, qos: int, interval: int):
        while self.periodic_publishing:
            try:
                self.publish_message(topic, message, qos)
            except Exception as e:
                print(f"Periodic publish error: {e}")
            time.sleep(interval)

    def stop_periodic_publish(self):
        self.periodic_publishing = False

    def get_messages(self, topic: Optional[str] = None, after_id: Optional[int] = None):
        with self.lock:
            messages = list(self.received_messages)

        if topic:
            messages = [msg for msg in messages if msg["topic"] == topic]

        if after_id is not None:
            messages = [msg for msg in messages if msg["id"] > after_id]

        return messages

    def get_status(self):
        with self.lock:
            return {
                "connected": self.connected,
                "periodic_publishing": self.periodic_publishing,
                "subscriptions": dict(self.subscriptions)
            }
        
    def get_message_history(
        self,
        topic: Optional[str] = None,
        direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ):
        return self.mqtt_message_repository.get_messages_paginated(
            topic=topic,
            direction=direction,
            page=page,
            page_size=page_size
        )