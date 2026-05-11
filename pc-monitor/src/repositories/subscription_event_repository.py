from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import SessionLocal
from src.models.subscription_event import SubscriptionEvent


class SubscriptionEventRepository:
    def add_event(self, topic: str, qos: int, action: str) -> None:
        db = SessionLocal()
        try:
            item = SubscriptionEvent(
                topic=topic,
                qos=qos,
                action=action
            )
            db.add(item)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
        finally:
            db.close()