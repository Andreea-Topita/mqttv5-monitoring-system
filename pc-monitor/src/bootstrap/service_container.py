from src.application.runtime.monitor_runtime import MonitorRuntime
from src.application.services.connection_service import ConnectionService
from src.application.services.message_service import MessageService
from src.application.services.monitor_facade import MonitorFacade
from src.application.services.publishing_service import PublishingService
from src.application.services.subscription_service import SubscriptionService
from src.infrastructure.repositories.connection_event_repository import (
    ConnectionEventRepository
)
from src.infrastructure.repositories.mqtt_message_repository import (
    MQTTMessageRepository
)
from src.infrastructure.repositories.subscription_event_repository import (
    SubscriptionEventRepository
)

from src.application.services.sensor_measurement_service import SensorMeasurementService
from src.infrastructure.repositories.sensor_measurement_repository import (
    SensorMeasurementRepository
)

# bootstrap = composition root
# leaga toate componentele intre ele, creeaza instantele si le injecteaza acolo unde e nevoie
runtime = MonitorRuntime()

# aici creez toate obiectele 
mqtt_message_repository = MQTTMessageRepository()
connection_event_repository = ConnectionEventRepository()
subscription_event_repository = SubscriptionEventRepository()
sensor_measurement_repository = SensorMeasurementRepository()

sensor_measurement_service = SensorMeasurementService(
    sensor_measurement_repository=sensor_measurement_repository
)

message_service = MessageService(
    runtime=runtime,
    mqtt_message_repository=mqtt_message_repository,
    sensor_measurement_service=sensor_measurement_service
)

connection_service = ConnectionService(
    runtime=runtime,
    connection_event_repository=connection_event_repository,
    on_message_callback=message_service.handle_incoming_message
)

publishing_service = PublishingService(
    runtime=runtime,
    mqtt_message_repository=mqtt_message_repository
)

subscription_service = SubscriptionService(
    runtime=runtime,
    subscription_event_repository=subscription_event_repository
)

monitor_service = MonitorFacade(
    connection_service=connection_service,
    publishing_service=publishing_service,
    subscription_service=subscription_service,
    message_service=message_service,
    sensor_measurement_service=sensor_measurement_service
)
