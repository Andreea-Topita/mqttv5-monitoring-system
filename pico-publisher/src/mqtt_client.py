import socket
import time

from mqtt_packets import MQTTPackets


class MQTTClientPico:
    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        client_id: str,
        username: str = "",
        password: str = "",
        keep_alive: int = 10,
        will_topic: str = None,
        will_payload: str = None,
        will_qos: int = 0,
    ):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.keep_alive = keep_alive
        self.will_topic = will_topic
        self.will_payload = will_payload
        self.will_qos = will_qos

        self.sock = None
        self.packet_builder = MQTTPackets()
        self.packet_id = 1
        self.last_ping = time.time()
        self.connected = False

    def connect(self):
        self.sock = socket.socket()
        self.sock.settimeout(2)
        self.sock.connect((self.broker_ip, self.broker_port))

        packet = self.packet_builder.connect_packet(
            client_id=self.client_id,
            username=self.username,
            password=self.password,
            keep_alive=self.keep_alive,
            will_topic=self.will_topic,
            will_payload=self.will_payload,
            will_qos=self.will_qos,
        )
        self.sock.send(packet)

        response = self.sock.recv(1024)
        if len(response) >= 4 and response[0] == 0x20 and response[3] == 0x00:
            self.connected = True
            print("CONNACK received")
        else:
            raise RuntimeError("Failed to connect to broker")

    def publish(self, topic: str, message: str, qos: int = 0):
        if not self.connected:
            raise RuntimeError("Client not connected")

        packet = self.packet_builder.publish_packet(self.packet_id, topic, message, qos)
        self.sock.send(packet)

        if qos > 0:
            self.packet_id += 1

    def ping(self):
        if not self.connected:
            return

        if time.time() - self.last_ping >= self.keep_alive:
            self.sock.send(self.packet_builder.pingreq_packet())
            self.last_ping = time.time()
            print("PINGREQ sent")

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        finally:
            self.connected = False