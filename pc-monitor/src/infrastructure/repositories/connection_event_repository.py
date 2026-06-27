from src.infrastructure.database.session_manager import session_scope
from src.infrastructure.models.connection_event import ConnectionEvent

# la conectare sau deconectare de la broker, se salveaza un eveniment in baza de date
class ConnectionEventRepository:
    def add_event(
        self,
        client_id: str,
        broker_address: str,
        broker_port: int,
        event_type: str
    ) -> None:
        with session_scope() as db:
            item = ConnectionEvent(
                client_id=client_id,
                broker_address=broker_address,
                broker_port=broker_port,
                event_type=event_type
            )
            db.add(item)