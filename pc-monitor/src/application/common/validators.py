import re
from typing import Optional

from src.domain.exceptions import (
    BusinessValidationError,
    InvalidQoSError,
    InvalidTopicError
)

MQTT_ROOT_TOPIC = "licenta"

# pentru a analiza topicul primit, extrage client_id si categoria, nu interpreteaza +
DEVICE_TOPIC_PATTERN = re.compile(
    r"^licenta/(?P<client_id>[A-Za-z0-9_-]+)/(?P<category>[A-Za-z0-9_-]+)$"
)

# pentru a valida id-ul dispozitivului
DEVICE_CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

# categorie, nume, unitate 
SENSOR_MEASUREMENT_CONFIG = {
    "temperatura": {
        "measurement_name": "temperature",
        "unit": "Cel",
        "min_value": -40,
        "max_value": 80
    },
    "umiditate": {
        "measurement_name": "humidity",
        "unit": "%RH",
        "min_value": 0,
        "max_value": 100
    }
}

# abonare automata la topicurile de baza pentru toate dispozitivele 
# cu QoS 2
DEFAULT_DEVICE_SUBSCRIPTIONS = {
    "licenta/+/status": 2,
    "licenta/+/temperatura": 2,
    "licenta/+/umiditate": 2
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


def validate_device_client_id(client_id: str):
    if not client_id or not client_id.strip():
        raise BusinessValidationError("Device client ID must not be empty.")

    if not DEVICE_CLIENT_ID_PATTERN.match(client_id.strip()):
        raise BusinessValidationError(
            "Device client ID may contain only letters, digits, _ and -."
        )

def parse_device_topic(topic: str) -> Optional[dict]:
    if not topic:
        return None

    # incarca sa extraga client_id si categoria din topicul de tip dispozitiv
    match = DEVICE_TOPIC_PATTERN.match(topic.strip())
    if not match:
        return None

    return {
        "client_id": match.group("client_id"),
        "category": match.group("category")
    }


def build_device_topic(client_id: str, category: str) -> str:
    validate_device_client_id(client_id)
    return f"{MQTT_ROOT_TOPIC}/{client_id}/{category}"

# build topicul de configuratie pentru un dispozitiv, folosind client_id
def build_device_config_topic(client_id: str) -> str:
    return build_device_topic(client_id, "config")

# verificam daca topicul este unul de tip dispozitiv
# adica incepe cu licenta/ si are un client_id valid
def is_sensor_topic(topic: str) -> bool:
    info = parse_device_topic(topic)

    if info is None:
        return False

    return info["category"] in SENSOR_MEASUREMENT_CONFIG

def is_status_topic(topic: str) -> bool:
    info = parse_device_topic(topic)

    if info is None:
        return False

    return info["category"] == "status"


def get_sensor_config_by_topic(topic: str):
    info = parse_device_topic(topic)

    if info is None:
        return None

    return SENSOR_MEASUREMENT_CONFIG.get(info["category"])

# validarea masuratorilor primite de la senzori
# conform configuratiei pentru fiecare categorie
def is_valid_sensor_measurement(
    topic: str,
    measurement_name: str,
    unit: str,
    value: float
) -> bool:
    config = get_sensor_config_by_topic(topic)

    if config is None:
        return False

    if measurement_name != config["measurement_name"]:
        return False

    if unit != config["unit"]:
        return False

    return config["min_value"] <= value <= config["max_value"]