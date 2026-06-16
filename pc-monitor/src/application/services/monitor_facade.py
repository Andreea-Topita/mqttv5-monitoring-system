from typing import Optional

from src.application.services.connection_service import ConnectionService
from src.application.services.message_service import MessageService
from src.application.services.publishing_service import PublishingService
from src.application.services.subscription_service import SubscriptionService
from src.application.services.sensor_measurement_service import SensorMeasurementService


# clasa care ofera o interfata comuna pentru toate serviciile, rutele folosesc doar monitor_service
# care e o instanta a acestei clase, si nu trebuie sa stie nimic despre celelalte servicii sau runtime
class MonitorFacade:
    def __init__(
        self,
        connection_service: ConnectionService,
        publishing_service: PublishingService,
        subscription_service: SubscriptionService,
        message_service: MessageService,
        sensor_measurement_service: SensorMeasurementService
    ):
        self.connection_service = connection_service
        self.publishing_service = publishing_service
        self.subscription_service = subscription_service
        self.message_service = message_service
        self.sensor_measurement_service = sensor_measurement_service

    # grupeaza metodele din celelalte servicii, astfel incat rutele sa aiba o interfata unica
    def connect(self, *args, **kwargs):
        return self.connection_service.connect(*args, **kwargs)

    def disconnect(self):
        return self.connection_service.disconnect()

    def get_status(self):
        return self.connection_service.get_status()
    
    def get_devices(self):
        return self.connection_service.get_devices()

    def publish_message(self, *args, **kwargs):
        return self.publishing_service.publish_message(*args, **kwargs)
    
    def configure_device(self, *args, **kwargs):
        return self.publishing_service.configure_device(*args, **kwargs)

    def start_periodic_publish(self, *args, **kwargs):
        return self.publishing_service.start_periodic_publish(*args, **kwargs)

    def stop_periodic_publish(self):
        return self.publishing_service.stop_periodic_publish()

    def subscribe(self, *args, **kwargs):
        return self.subscription_service.subscribe(*args, **kwargs)

    def unsubscribe(self, *args, **kwargs):
        return self.subscription_service.unsubscribe(*args, **kwargs)

    def get_messages(
        self,
        topic: Optional[str] = None,
        after_id: Optional[int] = None
    ):
        return self.message_service.get_live_messages(
            topic=topic,
            after_id=after_id
        )

    def get_message_history(
        self,
        topic: Optional[str] = None,
        direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ):
        return self.message_service.get_message_history(
            topic=topic,
            direction=direction,
            page=page,
            page_size=page_size
        )
    
    def get_sensor_measurements(
        self,
        measurement_name: Optional[str] = None,
        topic: Optional[str] = None,
        source_client_id: Optional[str] = None,
        limit: int = 50
    ):
        return self.sensor_measurement_service.get_measurements(
            measurement_name=measurement_name,
            topic=topic,
            source_client_id=source_client_id,
            limit=limit
        )