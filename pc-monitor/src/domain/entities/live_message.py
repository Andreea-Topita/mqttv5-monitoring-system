from dataclasses import dataclass

# obiect intern al aplicatiei, mesaj live tinut in memorie, nu mesaj in baza de date
@dataclass(slots=True)
class LiveMessage:
    id: int
    topic: str
    message: str
    timestamp: float