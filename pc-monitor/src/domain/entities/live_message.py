from dataclasses import dataclass

# obiect intern al aplicatiei 
@dataclass(slots=True)
class LiveMessage:
    id: int
    topic: str
    message: str
    timestamp: float