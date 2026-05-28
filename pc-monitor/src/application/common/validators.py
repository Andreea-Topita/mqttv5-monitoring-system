from src.domain.exceptions import (
    BusinessValidationError,
    InvalidQoSError,
    InvalidTopicError
)

SENSOR_TOPIC_CONFIG = {
    "licenta/pico/temperatura": {
        "measurement_name": "temperature",
        "unit": "Cel",
        "min_value": -40,
        "max_value": 80
    },
    "licenta/pico/umiditate": {
        "measurement_name": "humidity",
        "unit": "%RH",
        "min_value": 0,
        "max_value": 100
    }
}

def validate_topic(topic: str):
    if not topic or not topic.strip():
        raise InvalidTopicError("Topic must not be empty.")

def validate_qos(qos: int):
    if qos not in (0, 1, 2):
        raise InvalidQoSError("QoS must be 0, 1 or 2.")

def validate_interval(interval: int):
    if interval <= 0:
        raise BusinessValidationError("Interval must be greater than 0.")

def is_sensor_topic(topic: str) -> bool:
    return topic in SENSOR_TOPIC_CONFIG

def is_valid_sensor_measurement(
    topic: str,
    measurement_name: str,
    unit: str,
    value: float
) -> bool:
    config = SENSOR_TOPIC_CONFIG.get(topic)

    if config is None:
        return False

    if measurement_name != config["measurement_name"]:
        return False

    if unit != config["unit"]:
        return False

    return config["min_value"] <= value <= config["max_value"]
