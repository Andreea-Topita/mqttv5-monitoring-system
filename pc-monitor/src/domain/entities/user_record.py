from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class UserRecord:
    id: int
    username: str
    email: str
    password_hash: str
    created_at: datetime