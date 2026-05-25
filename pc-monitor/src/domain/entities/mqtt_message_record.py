from dataclasses import dataclass
from datetime import datetime

# forma unui mesaj salvat in baza de date
@dataclass(slots=True)
class MqttMessageRecord:
    id: int
    topic: str
    payload: str
    qos: int
    direction: str
    source_client_id: str | None
    created_at: datetime | None