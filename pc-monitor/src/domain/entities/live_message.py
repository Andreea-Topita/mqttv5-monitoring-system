from dataclasses import dataclass


@dataclass(slots=True)
class LiveMessage:
    id: int
    topic: str
    message: str
    timestamp: float