from src.application.common.persistence import persist_safely
from src.application.common.validators import validate_qos, validate_topic
from src.application.runtime.monitor_runtime import MonitorRuntime
from src.domain.enums.subscription_action import SubscriptionAction
from src.domain.exceptions import NotConnectedError, SubscriptionNotFoundError
from src.infrastructure.repositories.subscription_event_repository import (
    SubscriptionEventRepository
)

# abonari si dezabonari la topicuri, salvarea evenimentelor in baza de date
class SubscriptionService:
    def __init__(
        self,
        runtime: MonitorRuntime,
        subscription_event_repository: SubscriptionEventRepository
    ):
        self.runtime = runtime
        self.subscription_event_repository = subscription_event_repository

    def subscribe(self, topic: str, qos: int):
        if not self.runtime.client or not self.runtime.connected:
            raise NotConnectedError("Client is not connected to broker.")

        validate_topic(topic)
        validate_qos(qos)

        # abonare la topicul specificat cu qos-ul specificat, daca nu e deja abonat
        self.runtime.client.subscribe(topic, qos)

        # adaugare topic in lista de abonamente, pentru a fi afisat in UI si pentru a fi folosit la salvarea mesajelor
        self.runtime.set_subscription(topic, qos)

        persist_safely(
            "saving subscribe event",
            self.subscription_event_repository.add_event,
            topic=topic,
            qos=qos,
            action=SubscriptionAction.SUBSCRIBE.value
        )

    def unsubscribe(self, topic: str):
        if not self.runtime.client or not self.runtime.connected:
            raise NotConnectedError("Client is not connected to broker.")

        validate_topic(topic)

        if not self.runtime.has_subscription(topic):
            raise SubscriptionNotFoundError(
                f"Topic '{topic}' is not currently subscribed."
            )

        old_qos = self.runtime.get_subscription_qos(topic)

        self.runtime.client.unsubscribe(topic)

        self.runtime.remove_subscription(topic)

        persist_safely(
            "saving unsubscribe event",
            self.subscription_event_repository.add_event,
            topic=topic,
            qos=old_qos,
            action=SubscriptionAction.UNSUBSCRIBE.value
        )