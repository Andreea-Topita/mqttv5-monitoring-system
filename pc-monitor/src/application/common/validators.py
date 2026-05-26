from src.domain.exceptions import (
    BusinessValidationError,
    InvalidQoSError,
    InvalidTopicError
)


def validate_topic(topic: str):
    if not topic or not topic.strip():
        raise InvalidTopicError("Topic must not be empty.")


def validate_qos(qos: int):
    if qos not in (0, 1, 2):
        raise InvalidQoSError("QoS must be 0, 1 or 2.")


def validate_interval(interval: int):
    if interval <= 0:
        raise BusinessValidationError("Interval must be greater than 0.")