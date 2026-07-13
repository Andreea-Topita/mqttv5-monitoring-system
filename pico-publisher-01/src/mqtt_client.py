import socket
import time

try:
    import select
except ImportError:
    import uselect as select
    
from mqtt_packets import MQTTPackets
from mqtt_parser import MQTTPacketParser
try:
    import ssl
except Exception:
    ssl = None
    
class MQTTClientPico:
    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        client_id: str,
        username: str = "",
        password: str = "",
        keep_alive: int = 30,
        will_topic: str = None,
        will_payload: str = None,
        will_qos: int = 0,
        will_retain: bool = False,
        will_user_properties=None,
        use_tls: bool = False
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
        self.will_user_properties = will_user_properties
        self.use_tls = use_tls

        self.last_sent = time.time()
        self.last_received = time.time()
        self.sock = None
        self.packet_builder = MQTTPackets()
        self.packet_parser = MQTTPacketParser()

        self.packet_id = 1
        self.connected = False
        self.on_message_callback = None
        self.poller = None
        
        self.received_acks = {}
        
    # trimite toti octetii de pe socket
    def _send_all(self, data: bytes):
        total_sent = 0

        while total_sent < len(data):
            remaining_data = data[total_sent:]

            if hasattr(self.sock, "write"):
                sent = self.sock.write(remaining_data)
            else:
                sent = self.sock.send(remaining_data)

            if sent is None:
                raise OSError("Socket did not accept data")

            if sent <= 0:
                raise OSError("Socket connection broken")

            total_sent += sent

        self.last_sent = time.time()

    # citeste un pachet de la broker si returneaza un dictionar cu informatiile
    def _read_packet(self) -> dict:
        packet = self.packet_parser.read_packet(self.sock)
        self.last_received = time.time()
        return packet

    def _next_packet_id(self) -> int:
        current = self.packet_id
        self.packet_id += 1

        if self.packet_id > 65535:
            self.packet_id = 1

        return current
    
    def connect(self):
        raw_sock = socket.socket()

        # timeout folosit doar pentru stabilirea conexiunii TCP
        raw_sock.settimeout(10)
        raw_sock.connect((self.broker_ip, self.broker_port))

        # dupa conectare revenim la modul blocking
        # altfel socketul TLS mosteneste timeoutul si produce eroarea -110
        raw_sock.settimeout(None)

        if self.use_tls:
            if ssl is None:
                raise RuntimeError(
                    "SSL module is not available on this MicroPython firmware"
                )

            try:
                self.sock = ssl.wrap_socket(
                    raw_sock,
                    server_hostname=self.broker_ip
                )
            except TypeError:
                self.sock = ssl.wrap_socket(raw_sock)

            print("TLS socket created")
        else:
            self.sock = raw_sock
            print("TCP socket created")

        packet = self.packet_builder.connect_packet(
            client_id=self.client_id,
            username=self.username,
            password=self.password,
            keep_alive=self.keep_alive,
            will_topic=self.will_topic,
            will_payload=self.will_payload,
            will_qos=self.will_qos,
            will_retain=self.will_retain,
            will_user_properties=self.will_user_properties,
        )

        self._send_all(packet)

        response = self._read_packet()
        connack = self.packet_parser.parse_connack(response)

        if connack["reason_code"] == 0x00:
            self.connected = True
            
            # initializare poller pentru a putea verifica daca brokerul a trimis date fara sa blocheze aplicatia
            self.poller = select.poll()
            self.poller.register(self.sock, select.POLLIN)
            print("CONNACK received")
        else:
            raise RuntimeError(
                "Broker rejected connection, reason code={}".format(
                    connack["reason_code"]
                )
            )

    def _store_ack(
        self,
        packet_type: int,
        packet_id: int,
        reason_code: int = 0x00
    ):
        # salveaza confirmarea primita de la broker
        self.received_acks[(packet_type, packet_id)] = reason_code


    # daca exista conformarea, asteapta pana la timeout pentru a o primi, altfel arunca exceptie
    def _wait_for_ack(
        self,
        expected_type: int,
        expected_packet_id: int,
        timeout: int = 5
    ):
        # asteapta confirmarea care foloseste acelasi packet id
        start = time.time()

        while time.time() - start < timeout:
            reason_code = self.received_acks.pop(
                (expected_type, expected_packet_id),
                None
            )

            if reason_code is not None:
                if reason_code >= 0x80:
                    raise RuntimeError(
                        "Broker returned error reason code={}".format(
                            reason_code
                        )
                    )

                return {
                    "packet_id": expected_packet_id,
                    "reason_code": reason_code
                }

            # verifica daca brokerul a trimis un pachet
            self.loop_once(timeout_ms=100)

        raise RuntimeError(
            "Timeout waiting for ack packet id {}".format(
                expected_packet_id
            )
        )

    def publish(self, topic: str, message: str, qos: int = 0, retain: bool = False, user_properties=None):
        if not self.connected:
            raise RuntimeError("Client not connected")

        if qos == 0:
            packet = self.packet_builder.publish_packet(
                topic=topic,
                message=message,
                qos=0,
                retain=retain,
                user_properties=user_properties,
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
                user_properties=user_properties,
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
                user_properties=user_properties,
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
    
    def subscribe(self, topic: str, qos: int = 0):
        # trimite subscribe catre broker
        if not self.connected:
            raise RuntimeError("Client not connected")

        packet_id = self._next_packet_id()

        packet = self.packet_builder.subscribe_packet(
            topic=topic,
            qos=qos,
            packet_id=packet_id
        )

        self._send_all(packet)

        self._wait_for_ack(
            expected_type=self.packet_parser.TYPE_SUBACK,
            expected_packet_id=packet_id,
        )

        print("SUBACK received for topic", topic)

    def set_message_callback(self, on_message_callback):
        # salveaza functia apelata la primirea unui mesaj mqtt
        self.on_message_callback = on_message_callback


    def _handle_packet(self, packet: dict):
        # proceseaza un singur pachet primit de la broker

        if packet["type"] == self.packet_parser.TYPE_PINGRESP:
            print("PINGRESP received")
            return

        if packet["type"] == self.packet_parser.TYPE_DISCONNECT:
            info = self.packet_parser.parse_disconnect(packet)

            print(
                "Broker sent DISCONNECT, reason code={}".format(
                    info["reason_code"]
                )
            )

            self.connected = False
            return

        if packet["type"] == self.packet_parser.TYPE_SUBACK:
            # suback are o structura diferita fata de celelalte confirmari
            ack = self.packet_parser.parse_suback(packet)

            self._store_ack(
                packet_type=packet["type"],
                packet_id=ack["packet_id"],
                reason_code=ack["reason_code"]
            )
            return

        if packet["type"] in [
            self.packet_parser.TYPE_PUBACK,
            self.packet_parser.TYPE_PUBREC,
            self.packet_parser.TYPE_PUBCOMP
        ]:
            # proceseaza confirmarile pentru publicare
            ack = self.packet_parser.parse_ack(
                packet,
                packet["type"]
            )

            self._store_ack(
                packet_type=packet["type"],
                packet_id=ack["packet_id"],
                reason_code=ack["reason_code"]
            )
            return   

        if packet["type"] == self.packet_parser.TYPE_PUBLISH:
            publish_info = self.packet_parser.parse_publish(packet)

            topic = publish_info["topic"]
            message = publish_info["message"]
            qos = publish_info["qos"]
            packet_id = publish_info["packet_id"]

            print("config publish received")
            print("topic:", topic)
            print("message:", message)

            if self.on_message_callback:
                self.on_message_callback(topic, message)

            if qos == 1 and packet_id is not None:
                puback = self.packet_builder.puback_packet(packet_id)
                self._send_all(puback)
                print("PUBACK sent for config message")

            elif qos == 2 and packet_id is not None:
                pubrec = self.packet_builder.pubrec_packet(packet_id)
                self._send_all(pubrec)
                print("PUBREC sent for config message")

            return

        if packet["type"] == self.packet_parser.TYPE_PUBREL:
            ack = self.packet_parser.parse_ack(
                packet,
                self.packet_parser.TYPE_PUBREL
            )

            pubcomp = self.packet_builder.pubcomp_packet(
                ack["packet_id"]
            )

            self._send_all(pubcomp)
            print("PUBCOMP sent for config message")


    def loop_once(self, timeout_ms=0):
        # verifica daca brokerul a trimis date fara sa blocheze aplicatia

        if not self.connected or self.poller is None:
            return False

        events = self.poller.poll(timeout_ms)

        if not events:
            return False

        try:
            # citeste si proceseaza un singur pachet de la broker
            packet = self._read_packet()
            self._handle_packet(packet)
            return True

        except Exception:
            self.connected = False
            raise

    def ping(self):
        if not self.connected:
            return

        # keep alive se raporteaza la ultimul pachet trimis de client
        idle_time = time.time() - self.last_sent

        if idle_time < self.keep_alive:
            return

        self._send_all(self.packet_builder.pingreq_packet())
        print("PINGREQ sent")

    # daca close reuseste sa trimita disconnect, inchidere e normala
    # nu reusesti si conexiunea moare direct, brokerul considera ca e o cadere si publica mesajul de will 
    def close(self):
        try:
            if self.sock:
                try:
                    self._send_all(
                        self.packet_builder.disconnect_packet()
                    )
                except Exception:
                    pass

                try:
                    if self.poller:
                        self.poller.unregister(self.sock)
                except Exception:
                    pass

                self.sock.close()

        except Exception:
            pass

        finally:
            self.connected = False
            self.sock = None
            self.poller = None

