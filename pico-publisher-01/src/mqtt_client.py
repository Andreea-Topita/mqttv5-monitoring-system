import socket
import time
import _thread
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
        keep_alive: int = 10,
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

        self.last_activity = time.time()
        self.sock = None
        self.packet_builder = MQTTPackets()
        self.packet_parser = MQTTPacketParser()

        self.packet_id = 1
        self.connected = False
        self.on_message_callback = None
        self.receive_loop_running = False

        self.ack_lock = _thread.allocate_lock()
        self.send_lock = _thread.allocate_lock()
        self.received_acks = {}


    def _send_all(self, data: bytes):
        self.send_lock.acquire()

        try:
            total_sent = 0

            while total_sent < len(data):
                remaining_data = data[total_sent:]

                if hasattr(self.sock, "write"):
                    sent = self.sock.write(remaining_data)
                else:
                    sent = self.sock.send(remaining_data)

                if sent is None:
                    sent = len(remaining_data)

                if sent == 0:
                    raise OSError("Socket connection broken")

                total_sent += sent

            self.last_activity = time.time()

        finally:
            self.send_lock.release()
            
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
        raw_sock = socket.socket()

        # Timeout folosit doar pentru stabilirea conexiunii TCP.
        raw_sock.settimeout(10)
        raw_sock.connect((self.broker_ip, self.broker_port))

        # După conectare revenim la modul blocking.
        # Altfel socketul TLS moștenește timeoutul și produce eroarea -110.
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
            print("CONNACK received")
        else:
            raise RuntimeError(
                "Broker rejected connection, reason code={}".format(
                    connack["reason_code"]
                )
            )

    def _store_ack(self, packet_type: int, packet_id: int, reason_code: int = 0x00):
        # salvez confirmarile primite de la broker
        # publish/subscribe asteapta apoi confirmarea cu acelasi packet id
        self.ack_lock.acquire()
        try:
            self.received_acks[(packet_type, packet_id)] = reason_code
        finally:
            self.ack_lock.release()


    def _wait_for_ack(self, expected_type: int, expected_packet_id: int, timeout: int = 5):
        # asteapta confirmarea pentru un anumit packet id
        start = time.time()

        while time.time() - start < timeout:
            self.ack_lock.acquire()
            try:
                reason_code = self.received_acks.pop(
                    (expected_type, expected_packet_id),
                    None
                )
            finally:
                self.ack_lock.release()

            if reason_code is not None:
                if reason_code >= 0x80:
                    raise RuntimeError(
                        "Broker returned error reason code={}".format(reason_code)
                    )
                return {
                    "packet_id": expected_packet_id,
                    "reason_code": reason_code
                }

            time.sleep(0.05)

        raise RuntimeError("Timeout waiting for ack packet id {}".format(expected_packet_id))

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


    def start_receive_loop(self, on_message_callback):
        # porneste firul care asculta mesajele primite de la broker
        self.on_message_callback = on_message_callback
        self.receive_loop_running = True

        _thread.start_new_thread(self._receive_loop, ())


    def _receive_loop(self):
        # ruleaza in fundal si citeste pachetele venite de la broker
        print("Receive loop started")

        while self.connected and self.receive_loop_running:
            try:
                packet = self._read_packet()

                if packet["type"] == self.packet_parser.TYPE_PINGRESP:
                    print("PINGRESP received")
                    continue

                if packet["type"] == self.packet_parser.TYPE_DISCONNECT:
                    info = self.packet_parser.parse_disconnect(packet)
                    print("Broker sent DISCONNECT, reason code={}".format(info["reason_code"]))
                    self.connected = False
                    break

                if packet["type"] in [
                    self.packet_parser.TYPE_PUBACK,
                    self.packet_parser.TYPE_PUBREC,
                    self.packet_parser.TYPE_PUBCOMP,
                    self.packet_parser.TYPE_SUBACK
                ]:
                    ack = self.packet_parser.parse_ack(packet, packet["type"])
                    self._store_ack(
                        packet_type=packet["type"],
                        packet_id=ack["packet_id"],
                        reason_code=ack["reason_code"]
                    )
                    continue

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

                    continue

                if packet["type"] == self.packet_parser.TYPE_PUBREL:
                    ack = self.packet_parser.parse_ack(
                        packet,
                        self.packet_parser.TYPE_PUBREL
                    )

                    pubcomp = self.packet_builder.pubcomp_packet(ack["packet_id"])
                    self._send_all(pubcomp)
                    print("PUBCOMP sent for config message")
                    continue
                
            except OSError as e:
                error_code = e.args[0] if len(e.args) > 0 else None

                # Unele versiuni MicroPython întorc 110,
                # iar altele întorc -110 pentru timeout.
                if error_code in (110, -110):
                    time.sleep(0.05)
                    continue

                print("receive loop os error:", e)
                self.connected = False
                break
                
            except Exception as e:
                print("receive loop error:", e)
                self.connected = False
                break

        print("Receive loop stopped")


    def ping(self):
        if not self.connected:
            return

        idle_time = time.time() - self.last_activity
        if idle_time < self.keep_alive:
            return

        self._send_all(self.packet_builder.pingreq_packet())
        print("PINGREQ sent")

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