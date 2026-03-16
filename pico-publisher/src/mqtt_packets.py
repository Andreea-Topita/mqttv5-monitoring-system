class MQTTPackets:
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
    ) -> bytes:
        packet = bytearray()
        packet.append(0x10)
        packet.append(0x00)  # placeholder remaining length

        # Variable header
        packet.extend(b"\x00\x04")
        packet.extend(b"MQTT")
        packet.append(0x05)

        # Connect flags
        connect_flags = 0x02

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

        packet.append(connect_flags)
        packet.extend(int(keep_alive).to_bytes(2, "big"))

        # Properties length = 0
        packet.append(0x00)

        # Payload
        packet.extend(len(client_id).to_bytes(2, "big"))
        packet.extend(client_id.encode())

        if will_flag:
            packet.append(0x00)  # will properties length
            packet.extend(len(will_topic).to_bytes(2, "big"))
            packet.extend(will_topic.encode())
            packet.extend(len(will_payload).to_bytes(2, "big"))
            packet.extend(will_payload.encode())

        if username:
            packet.extend(len(username).to_bytes(2, "big"))
            packet.extend(username.encode())

        if password:
            packet.extend(len(password).to_bytes(2, "big"))
            packet.extend(password.encode())

        remaining_length = len(packet) - 2
        packet[1] = remaining_length
        return bytes(packet)

    def publish_packet(self, packet_id: int, topic: str, message: str, qos: int = 0) -> bytes:
        packet = bytearray()

        flags = 0x30
        if qos == 1:
            flags |= 0x02
        elif qos == 2:
            flags |= 0x04
        elif qos != 0:
            raise ValueError("Invalid QoS")

        packet.append(flags)
        packet.append(0x00)  # placeholder remaining length

        packet.extend(len(topic).to_bytes(2, "big"))
        packet.extend(topic.encode())

        if qos > 0:
            packet.extend(packet_id.to_bytes(2, "big"))

        # Properties length = 0
        packet.append(0x00)

        packet.extend(message.encode())

        remaining_length = len(packet) - 2
        packet[1] = remaining_length
        return bytes(packet)

    def pingreq_packet(self) -> bytes:
        return b"\xC0\x00"