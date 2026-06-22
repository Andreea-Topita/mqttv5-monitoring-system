class MQTTPackets:
    def _encode_varint(self, value: int) -> bytes:
        encoded = bytearray()

        while True:
            digit = value % 128     # ia urmatorii 7 biti
            value //= 128          # muta mai departe ce a ramas din valoare

            if value > 0: 
                digit |= 0x80   # daca a mai ramas ceva, seteaza bitul de continuare

            encoded.append(digit)

            if value == 0:
                break

        return bytes(encoded)

    # prefix de 2 octeti pentru lungimea stringului, urmat de stringul propriu-zis
    def _encode_utf8(self, text: str) -> bytes:
        data = text.encode()
        return len(data).to_bytes(2, "big") + data

    def connect_packet(
        self,
        client_id: str,
        username: str,
        password: str,
        keep_alive: int = 10,
        will_topic: str = None,
        will_payload: str = None,
        will_qos: int = 0,
        will_retain: bool = False,
        will_user_properties=None,
    ) -> bytes:
        variable_header = bytearray()
        variable_header.extend(b"\x00\x04")
        variable_header.extend(b"MQTT")
        variable_header.append(0x05)

        connect_flags = 0x02  # clean start

        if username:
            connect_flags |= 0x80
        if password:
            connect_flags |= 0x40

        will_flag = will_topic is not None and will_payload is not None
        if will_flag:
            connect_flags |= 0x04
            connect_flags |= (will_qos & 0x03) << 3
            if will_retain:
                connect_flags |= 0x20

        variable_header.append(connect_flags)
        variable_header.extend(int(keep_alive).to_bytes(2, "big"))
        variable_header.extend(self._encode_varint(0))  # connect properties length = 0

        payload = bytearray()
        payload.extend(self._encode_utf8(client_id))

        if will_flag:
            will_properties = self._encode_user_properties(will_user_properties)
            payload.extend(self._encode_varint(len(will_properties)))
            payload.extend(will_properties)
            payload.extend(self._encode_utf8(will_topic))
            payload.extend(self._encode_utf8(will_payload))

        if username:
            payload.extend(self._encode_utf8(username))

        if password:
            payload.extend(self._encode_utf8(password))

        remaining_length = len(variable_header) + len(payload)

        packet = bytearray()
        packet.append(0x10)
        packet.extend(self._encode_varint(remaining_length))
        packet.extend(variable_header)
        packet.extend(payload)

        return bytes(packet)

    def publish_packet(
        self,
        topic: str,
        message: str,
        qos: int = 0,
        packet_id: int = None,
        dup: bool = False,
        retain: bool = False,
        user_properties=None,
    ) -> bytes:
        if qos not in (0, 1, 2):
            raise ValueError("Invalid QoS")

        flags = 0x30
        if dup:
            flags |= 0x08
        if qos == 1:
            flags |= 0x02
        elif qos == 2:
            flags |= 0x04
        if retain:
            flags |= 0x01

        variable_header = bytearray()
        variable_header.extend(self._encode_utf8(topic))

        if qos > 0:
            if packet_id is None or packet_id == 0:
                raise ValueError("packet_id is required for QoS > 0")
            variable_header.extend(packet_id.to_bytes(2, "big"))

        properties = self._encode_user_properties(user_properties)
        variable_header.extend(self._encode_varint(len(properties)))
        variable_header.extend(properties)

        payload = message.encode()
        remaining_length = len(variable_header) + len(payload)

        packet = bytearray()
        packet.append(flags)
        packet.extend(self._encode_varint(remaining_length))
        packet.extend(variable_header)
        packet.extend(payload)

        return bytes(packet)

    def pingreq_packet(self) -> bytes:
        return b"\xC0\x00"

    def pubrel_packet(self, packet_id: int) -> bytes:
        packet = bytearray()
        packet.append(0x62)  # PUBREL fixed header
        packet.append(0x02)  # remaining length = 2
        packet.extend(packet_id.to_bytes(2, "big"))
        return bytes(packet)

    def disconnect_packet(self) -> bytes:
        return b"\xE0\x00"
    
    def _encode_user_properties(self, user_properties):
        props = bytearray()

        if not user_properties:
            return bytes(props)

        for key, value in user_properties.items():
            props.append(0x26)  # User Property identifier
            props.extend(self._encode_utf8(str(key)))
            props.extend(self._encode_utf8(str(value)))

        return bytes(props)
    
    def subscribe_packet(self, topic: str, qos: int, packet_id: int) -> bytes:
        # construiesc pachetul subscribe pentru mqtt v5
        packet = bytearray()

        # fixed header pentru subscribe este 0x82
        packet.append(0x82)

        variable_header = bytearray()

        # packet id, necesar pentru subscribe
        variable_header.extend(packet_id.to_bytes(2, "big"))

        # property length = 0 pentru ca nu trimit proprietati
        variable_header.append(0x00)

        payload = bytearray()

        # topicul la care vreau sa ma abonez
        payload.extend(len(topic).to_bytes(2, "big"))
        payload.extend(topic.encode("utf-8"))

        # optiunile de subscribe, aici doar qos-ul
        payload.append(qos)

        remaining_length = len(variable_header) + len(payload)

        # la topicurile noastre lungimea incape intr-un singur byte
        packet.append(remaining_length)

        packet.extend(variable_header)
        packet.extend(payload)

        return bytes(packet)
    
    def puback_packet(self, packet_id: int) -> bytes:
        # raspuns pentru publish primit cu qos 1
        return bytes([0x40, 0x02]) + packet_id.to_bytes(2, "big")


    def pubrec_packet(self, packet_id: int) -> bytes:
        # primul raspuns pentru publish primit cu qos 2
        return bytes([0x50, 0x02]) + packet_id.to_bytes(2, "big")


    def pubcomp_packet(self, packet_id: int) -> bytes:
        # ultimul raspuns pentru publish primit cu qos 2
        return bytes([0x70, 0x02]) + packet_id.to_bytes(2, "big")