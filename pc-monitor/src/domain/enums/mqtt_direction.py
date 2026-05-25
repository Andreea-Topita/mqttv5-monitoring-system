from enum import StrEnum


class MqttDirection(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"