from enum import StrEnum


class ConnectionEventType(StrEnum):
    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"