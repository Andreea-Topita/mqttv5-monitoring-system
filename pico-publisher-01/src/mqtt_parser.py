class MQTTPacketParser:
    TYPE_CONNACK = 2
    TYPE_PUBLISH = 3
    TYPE_PUBACK = 4
    TYPE_PUBREC = 5
    TYPE_PUBREL = 6
    TYPE_PUBCOMP = 7
    TYPE_SUBACK = 9
    TYPE_PINGRESP = 13
    TYPE_DISCONNECT = 14

    #raspunsurile brokerului
    def _read_exact(self, sock, size: int) -> bytes:
        data = bytearray()

        while len(data) < size:
            remaining_size = size - len(data)

            if hasattr(sock, "read"):
                chunk = sock.read(remaining_size)
            else:
                chunk = sock.recv(remaining_size)

            if chunk is None:
                continue

            if not chunk:
                raise OSError("Socket closed by broker")

            data.extend(chunk)

        return bytes(data)

    def _read_varint(self, sock) -> int:
        multiplier = 1
        value = 0

        while True:
            encoded_byte = self._read_exact(sock, 1)[0]
            value += (encoded_byte & 0x7F) * multiplier

            if (encoded_byte & 0x80) == 0:
                break

            multiplier *= 128
            if multiplier > 128 * 128 * 128:
                raise ValueError("Malformed Remaining Length")

        return value

    def read_packet(self, sock) -> dict:
        first_byte = self._read_exact(sock, 1)[0]
        packet_type = first_byte >> 4
        flags = first_byte & 0x0F

        remaining_length = self._read_varint(sock)
        body = self._read_exact(sock, remaining_length)

        return {
            "type": packet_type,
            "flags": flags,
            "remaining_length": remaining_length,
            "body": body,
        }

    def parse_connack(self, packet: dict) -> dict:
        if packet["type"] != self.TYPE_CONNACK:
            raise ValueError("Expected CONNACK")

        body = packet["body"]
        if len(body) < 3:
            raise ValueError("Invalid CONNACK")

        session_present = body[0] & 0x01
        reason_code = body[1]

        return {
            "session_present": session_present,
            "reason_code": reason_code,
        }

    def parse_ack(self, packet: dict, expected_type: int) -> dict:
        if packet["type"] != expected_type:
            raise ValueError("Unexpected packet type")

        body = packet["body"]
        if len(body) < 2:
            raise ValueError("Invalid ACK packet")

        packet_id = int.from_bytes(body[0:2], "big")
        reason_code = body[2] if len(body) >= 3 else 0x00

        return {
            "packet_id": packet_id,
            "reason_code": reason_code,
        }

    def parse_pingresp(self, packet: dict) -> bool:
        if packet["type"] != self.TYPE_PINGRESP:
            raise ValueError("Expected PINGRESP")

        if packet["remaining_length"] != 0:
            raise ValueError("Invalid PINGRESP")

        return True

    def parse_disconnect(self, packet: dict) -> dict:
        if packet["type"] != self.TYPE_DISCONNECT:
            raise ValueError("Expected DISCONNECT")

        body = packet["body"]
        reason_code = body[0] if len(body) >= 1 else 0x00

        return {
            "reason_code": reason_code,
        }
    
    def _read_varint_from_bytes(self, data: bytes, start_index: int):
        # citeste un variable byte integer dintr-un sir de bytes
        multiplier = 1
        value = 0
        index = start_index

        while True:
            encoded_byte = data[index]
            value += (encoded_byte & 0x7F) * multiplier
            index += 1

            if (encoded_byte & 0x80) == 0:
                break

            multiplier *= 128
            if multiplier > 128 * 128 * 128:
                raise ValueError("Malformed variable byte integer")

        return value, index

    def parse_suback(self, packet: dict) -> dict:
        # parseaza raspunsul primit pentru subscribe
        if packet["type"] != self.TYPE_SUBACK:
            raise ValueError("Expected SUBACK")

        body = packet["body"]

        # suback trebuie sa contina packet id property length si reason code
        if len(body) < 4:
            raise ValueError("Invalid SUBACK")

        # primii doi octeti reprezinta identificatorul pachetului
        packet_id = int.from_bytes(body[0:2], "big")

        # dupa packet id urmeaza lungimea proprietatilor mqtt v5
        properties_length, index = self._read_varint_from_bytes(
            body,
            2
        )

        # sarim peste proprietatile primite
        index += properties_length

        # dupa proprietati trebuie sa existe rezultatul abonarii
        if index >= len(body):
            raise ValueError("SUBACK does not contain a reason code")

        reason_code = body[index]

        return {
            "packet_id": packet_id,
            "reason_code": reason_code
        }
    
    def parse_publish(self, packet: dict) -> dict:
        # parseaza un pachet publish primit de la broker
        if packet["type"] != self.TYPE_PUBLISH:
            raise ValueError("Expected PUBLISH")

        body = packet["body"]
        qos = (packet["flags"] & 0x06) >> 1

        index = 0

        # topic length
        topic_length = int.from_bytes(body[index:index + 2], "big")
        index += 2

        # topic
        topic = body[index:index + topic_length].decode("utf-8")
        index += topic_length

        packet_id = None

        # pentru qos 1 si qos 2 exista packet id
        if qos > 0:
            packet_id = int.from_bytes(body[index:index + 2], "big")
            index += 2

        # mqtt v5 are properties length dupa topic/packet id
        properties_length, index = self._read_varint_from_bytes(body, index)

        # sar peste proprietati
        index += properties_length

        # restul este payload-ul
        message = body[index:].decode("utf-8")

        return {
            "topic": topic,
            "message": message,
            "qos": qos,
            "packet_id": packet_id
        }
