from src.domain.entities.mqtt_message_record import MqttMessageRecord
from src.infrastructure.models.mqtt_message import MQTTMessage

# transforma model sql alchemy MQTTMessage intr-un record de domeniu MqttMessageRecord
def to_mqtt_message_record(item: MQTTMessage) -> MqttMessageRecord:
    return MqttMessageRecord(
        id=item.id,
        topic=item.topic,
        payload=item.payload,
        qos=item.qos,
        direction=item.direction,
        source_client_id=item.source_client_id,
        created_at=item.created_at
    )