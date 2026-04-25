import socket
import time

from mqtt_packets import MQTTPackets
from mqtt_parser import MQTTPacketParser

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
        will_retain: bool = False,
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
        self.will_retain = will_retain


        self.last_activity = time.time()
        self.sock = None
        self.packet_builder = MQTTPackets()
        self.packet_parser = MQTTPacketParser()

        self.packet_id = 1
        self.connected = False

    def _send_all(self, data: bytes):
        total_sent = 0

        while total_sent < len(data):
            sent = self.sock.send(data[total_sent:])
            if sent == 0:
                raise OSError("Socket connection broken")
            total_sent += sent

        self.last_activity = time.time()

    def _read_packet(self) -> dict:
        packet = self.packet_parser.read_packet(self.sock)
        self.last_activity = time.time()
        return packet

    def _next_packet_id(self) -> int:
        current = self.packet_id
        self.packet_id += 1

        if self.packet_id > 65535:
            self.packet_id = 1

        return current
    
    def connect(self):
        self.sock = socket.socket()
        self.sock.settimeout(5)
        self.sock.connect((self.broker_ip, self.broker_port))

        packet = self.packet_builder.connect_packet(
            client_id=self.client_id,
            username=self.username,
            password=self.password,
            keep_alive=self.keep_alive,
            will_topic=self.will_topic,
            will_payload=self.will_payload,
            will_qos=self.will_qos,
            will_retain=self.will_retain,
        )
        self._send_all(packet)

        response = self._read_packet()
        connack = self.packet_parser.parse_connack(response)

        if connack["reason_code"] == 0x00:
            self.connected = True
            print("CONNACK received")
        else:
            raise RuntimeError(
                "Broker rejected connection, reason code={}".format(connack["reason_code"])
            )

    def _wait_for_ack(self, expected_type: int, expected_packet_id: int):
        while True:
            packet = self._read_packet()

            if packet["type"] == self.packet_parser.TYPE_PINGRESP:
                print("PINGRESP received")
                continue

            if packet["type"] == self.packet_parser.TYPE_DISCONNECT:
                info = self.packet_parser.parse_disconnect(packet)
                raise RuntimeError(
                    "Broker sent DISCONNECT, reason code={}".format(info["reason_code"])
                )

            ack = self.packet_parser.parse_ack(packet, expected_type)

            if ack["packet_id"] != expected_packet_id:
                raise RuntimeError(
                    "Unexpected packet id: expected {}, got {}".format(
                        expected_packet_id, ack["packet_id"]
                    )
                )

            if ack["reason_code"] >= 0x80:
                raise RuntimeError(
                    "Broker returned error reason code={}".format(ack["reason_code"])
                )

            return ack

    def publish(self, topic: str, message: str, qos: int = 0, retain: bool = False):
        if not self.connected:
            raise RuntimeError("Client not connected")

        if qos == 0:
            packet = self.packet_builder.publish_packet(
                topic=topic,
                message=message,
                qos=0,
                retain=retain,
            )
            self._send_all(packet)
            return

        if qos == 1:
            packet_id = self._next_packet_id()

            packet = self.packet_builder.publish_packet(
                topic=topic,
                message=message,
                qos=1,
                packet_id=packet_id,
                retain=retain,
            )
            self._send_all(packet)

            self._wait_for_ack(
                expected_type=self.packet_parser.TYPE_PUBACK,
                expected_packet_id=packet_id,
            )
            print("PUBACK received for packet id", packet_id)
            return

        if qos == 2:
            packet_id = self._next_packet_id()

            packet = self.packet_builder.publish_packet(
                topic=topic,
                message=message,
                qos=2,
                packet_id=packet_id,
                retain=retain,
            )
            self._send_all(packet)

            self._wait_for_ack(
                expected_type=self.packet_parser.TYPE_PUBREC,
                expected_packet_id=packet_id,
            )
            print("PUBREC received for packet id", packet_id)

            pubrel = self.packet_builder.pubrel_packet(packet_id)
            self._send_all(pubrel)

            self._wait_for_ack(
                expected_type=self.packet_parser.TYPE_PUBCOMP,
                expected_packet_id=packet_id,
            )
            print("PUBCOMP received for packet id", packet_id)
            return

        raise ValueError("Invalid QoS")


    def ping(self):
        if not self.connected:
            return

        idle_time = time.time() - self.last_activity
        if idle_time < self.keep_alive:
            return

        self._send_all(self.packet_builder.pingreq_packet())
        print("PINGREQ sent")

        packet = self._read_packet()
        self.packet_parser.parse_pingresp(packet)
        print("PINGRESP received")

    # daca close reuseste sa trimita disconnect, inchidere e normala
    # daca nu reusesti si conexiunea moare direct, brokerul considera ca e o cadere si publica mesajul de will 
    def close(self):
        try:
            if self.sock:
                try:
                    self._send_all(self.packet_builder.disconnect_packet())
                except:
                    pass
                self.sock.close()
        except:
            pass
        finally:
            self.connected = False
            self.sock = None