from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import SessionLocal
from src.models.connection_event import ConnectionEvent


class ConnectionEventRepository:
    def add_event(
        self,
        client_id: str,
        broker_address: str,
        broker_port: int,
        event_type: str
    ) -> None:
        db = SessionLocal()
        try:
            item = ConnectionEvent(
                client_id=client_id,
                broker_address=broker_address,
                broker_port=broker_port,
                event_type=event_type
            )
            db.add(item)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
        finally:
            db.close()