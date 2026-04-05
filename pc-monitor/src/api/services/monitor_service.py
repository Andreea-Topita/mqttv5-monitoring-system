import threading
import time
from typing import Optional

from src.client.mqtt_client import MQTTClient
from src.monitoring.system_metrics import get_system_metric


class MonitorService:
    def __init__(self, on_message_callback=None):
        self.client = None
        self.connected = False
        self.periodic_publishing = False
        self.external_on_message_callback = on_message_callback
        
        # mesaje primite de la broker
        self.received_messages = []
        #numar crescutor pentru fiecare mesaj primit, pentru identificare
        self.message_counter = 0

        # topic -> qos, la ce topicuri suntem abonati si cu ce qos
        self.subscriptions = {}

        self.lock = threading.Lock()

    def _handle_incoming_message(self, topic: str, message: str):
        with self.lock:
            self.message_counter += 1
            self.received_messages.append({
                "id": self.message_counter,
                "topic": topic,
                "message": message,
                "timestamp": time.time()
            })

            # doar ultimele 200 mesaje
            if len(self.received_messages) > 200:
                self.received_messages.pop(0)

        # daca exista callback extern 
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
        self.client = MQTTClient(
            client_id=client_id,
            on_message_callback=self._handle_incoming_message
        )
        self.client.will_set(last_will_topic, last_will_message, qos=last_will_qos, retain=last_will_retain)
        self.client.username_pw_set(username, password)
        self.client.conectare_broker(broker_address, broker_port)
        self.connected = True

    def disconnect(self):
        if self.client and self.connected:
            self.client.disconnect()
            self.connected = False
            self.periodic_publishing = False

    def publish_metric(self, topic: str, qos: int):
        if not self.client or not self.connected:
            raise RuntimeError("Not connected to broker.")

        message = get_system_metric(topic)
        self.client.publish(topic, message, qos)
        return message

    def subscribe(self, topic: str, qos: int):
        if not self.client or not self.connected:
            raise RuntimeError("Not connected to broker.")

        self.client.subscribe(topic, qos)

        with self.lock:
            self.subscriptions[topic] = qos

    def unsubscribe(self, topic: str):
        if not self.client or not self.connected:
            raise RuntimeError("Not connected to broker.")

        self.client.unsubscribe(topic)

        with self.lock:
            if topic in self.subscriptions:
                del self.subscriptions[topic]

    def start_periodic_publish(self, topic: str, qos: int, interval: int = 5):
        if not self.connected:
            raise RuntimeError("Not connected to broker.")

        self.periodic_publishing = True
        threading.Thread(
            target=self._publish_periodically,
            args=(topic, qos, interval),
            daemon=True
        ).start()

    def _publish_periodically(self, topic: str, qos: int, interval: int):
        while self.periodic_publishing:
            try:
                self.publish_metric(topic, qos)
            except Exception as e:
                print(f"Periodic publish error: {e}")
            time.sleep(interval)

    def stop_periodic_publish(self):
        self.periodic_publishing = False

    # pentru UI, sa vedem ce mesaje am primit de la broker
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
                "subscriptions": self.subscriptions
            }