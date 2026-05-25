from src.infrastructure.database.session_manager import session_scope
from src.infrastructure.models.connection_event import ConnectionEvent


class ConnectionEventRepository:
    def add_event(
        self,
        client_id: str,
        broker_address: str,
        broker_port: int,
        event_type: str
    ) -> ConnectionEvent:
        with session_scope() as db:
            item = ConnectionEvent(
                client_id=client_id,
                broker_address=broker_address,
                broker_port=broker_port,
                event_type=event_type
            )
            db.add(item)
            db.flush()
            db.refresh(item)
            return item