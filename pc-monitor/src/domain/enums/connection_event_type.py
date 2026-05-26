from enum import StrEnum

# pentru servicii, in loc de stringuri simple, folosim enum uri
class ConnectionEventType(StrEnum):
    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"