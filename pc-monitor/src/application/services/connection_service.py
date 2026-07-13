from src.application.common.persistence import persist_safely
from src.application.common.validators import (
    DEFAULT_DEVICE_SUBSCRIPTIONS,
    validate_qos,
    validate_topic
)
from src.application.runtime.monitor_runtime import MonitorRuntime
from src.domain.enums.connection_event_type import ConnectionEventType
from src.domain.exceptions import (
    AlreadyConnectedError,
    BusinessValidationError,
    ConnectionFailedError,
    NotConnectedError
)
from src.infrastructure.mqtt.mqtt_client import MQTTClient
from src.infrastructure.repositories.connection_event_repository import (
    ConnectionEventRepository
)

# conectarea si deconectarea backend ului la brokerul mqtt 
class ConnectionService:
    def __init__(
        self,
        runtime: MonitorRuntime,
        connection_event_repository: ConnectionEventRepository,
        on_message_callback
    ):
        self.runtime = runtime
        self.connection_event_repository = connection_event_repository
        self.on_message_callback = on_message_callback

    # cand apas connect => se apeleaza aceasta metoda, care creeaza instanta clientului mqtt
    # seteaza callback ul pentru mesajele primite, seteaza last will, username si parola, si incearca sa se conecteze la broker
    def connect(
        self,
        broker_address: str,
        broker_port: int,
        client_id: str,
        username: str,
        password: str,
        last_will_topic: str,
        last_will_message: str,
        last_will_qos: int,
        last_will_retain: bool = False,
        use_tls: bool = False,
        tls_insecure: bool = False,
    ):
        if self.runtime.connected:
            raise AlreadyConnectedError("Client is already connected to a broker.")

        if not broker_address or not broker_address.strip():
            raise BusinessValidationError("Broker address must not be empty.")

        if not client_id or not client_id.strip():
            raise BusinessValidationError("Client ID must not be empty.")

        validate_topic(last_will_topic)

        if not last_will_message or not last_will_message.strip():
            raise BusinessValidationError("Last will message must not be empty.")

        validate_qos(last_will_qos)

        self.runtime.reset_live_state()

        self.runtime.client_id = client_id
        self.runtime.broker_address = broker_address
        self.runtime.broker_port = broker_port

        try:
            # creare client mqtt si callback pentru mesajele primite
            # cand vine un mesaj mqtt, se apeleaza callback ul, care la randul lui apeleaza MessageService.handle_incoming_message
            self.runtime.client = MQTTClient(
                client_id=client_id,
                on_message_callback=self.on_message_callback
            )
            
            self.runtime.client.tls_set(
                use_tls=use_tls,
                ca_cert_path="/app/certs/ca.crt",
                tls_insecure=tls_insecure
            )

            self.runtime.client.will_set(
                last_will_topic,
                last_will_message,
                qos=last_will_qos,
                retain=last_will_retain
            )

            self.runtime.client.username_pw_set(username, password)

            # deschidere conexiune tcp tls si trimitere pachet connect catre broker, daca nu reuseste, se arunca exceptie
            self.runtime.client.conectare_broker(
                broker_address,
                broker_port
            )

            self.runtime.connected = True

            # auto-subscribe la topicurile standard pentru dispozitive
            # daca nu reusesc sa ma abonez, afisez eroarea in consola, dar nu opresc conectarea
            for topic_filter, qos in DEFAULT_DEVICE_SUBSCRIPTIONS.items():
                try:
                    self.runtime.client.subscribe(topic_filter, qos)
                    # salveaza in memoria aplicatiei faptul ca abonamentul e activ 
                    self.runtime.set_subscription(topic_filter, qos)
                    print(f"Auto-subscribed to {topic_filter} with QoS {qos}.")
                except Exception as subscribe_error:
                    print(
                        f"Could not auto-subscribe to {topic_filter}: "
                        f"{subscribe_error}"
                    )
            # abonare automata la licenta/+/status... , pentru a detecta automat dispozitivele care publica pe aceste topicuri

        except Exception as e:
            self.runtime.client = None
            self.runtime.connected = False
            raise ConnectionFailedError(f"Failed to connect to broker: {e}")

        persist_safely(
            "saving connect event",
            self.connection_event_repository.add_event,
            client_id=client_id,
            broker_address=broker_address,
            broker_port=broker_port,
            event_type=ConnectionEventType.CONNECT.value
        )

    def disconnect(self):
        if not self.runtime.client or not self.runtime.connected:
            raise NotConnectedError("Client is not connected to any broker.")

        try:
            self.runtime.client.disconnect()
        finally:
            persist_safely(
                "saving disconnect event",
                self.connection_event_repository.add_event,
                client_id=self.runtime.client_id,
                broker_address=self.runtime.broker_address,
                broker_port=self.runtime.broker_port,
                event_type=ConnectionEventType.DISCONNECT.value
            )

        self.runtime.connected = False
        self.runtime.periodic_publishing = False
        self.runtime.client = None
        self.runtime.clear_subscriptions()

    # returneaza statusul curent al conexiunii, periodic publishing, 
    # abonamente si dispozitive, iar frontend ul poate folosi aceste informatii 
    # pentru a afisa starea curenta a aplicatiei
    def get_status(self):
        return {
            "connected": self.runtime.connected,
            "periodic_publishing": self.runtime.periodic_publishing,
            "subscriptions": self.runtime.get_subscriptions_copy(),
            "devices": self.runtime.get_devices_copy()
        }

    def get_devices(self):
        return self.runtime.get_devices_copy()