from src.infrastructure.database.session_manager import session_scope
from src.infrastructure.models.subscription_event import SubscriptionEvent


class SubscriptionEventRepository:
    def add_event(
        self,
        topic: str,
        qos: int,
        action: str
    ) -> None:
        with session_scope() as db:
            item = SubscriptionEvent(
                topic=topic,
                qos=qos,
                action=action
            )
            db.add(item)