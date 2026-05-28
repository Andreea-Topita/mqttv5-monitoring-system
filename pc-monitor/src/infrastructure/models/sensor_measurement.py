from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.sql import func

from src.infrastructure.database.connection import Base


class SensorMeasurement(Base):
    __tablename__ = "sensor_measurements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    mqtt_message_id = Column(
        BigInteger,
        ForeignKey("mqtt_messages.id", ondelete="SET NULL"),
        nullable=True
    )

    topic = Column(String(255), nullable=False)
    source_client_id = Column(String(100), nullable=True)

    base_name = Column(String(255), nullable=True)
    measurement_name = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    numeric_value = Column(Float, nullable=False)

    measured_at = Column(DateTime(timezone=False), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_sensor_measurements_measurement_time", "measurement_name", "measured_at"),
        Index("idx_sensor_measurements_topic_time", "topic", "measured_at"),
        Index("idx_sensor_measurements_source_time", "source_client_id", "measured_at"),
    )