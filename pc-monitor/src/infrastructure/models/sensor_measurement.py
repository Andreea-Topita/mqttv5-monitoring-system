from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.sql import func

from src.infrastructure.database.connection import Base

# pastreaza valorile numerice extrase din mesajele senML
class SensorMeasurement(Base):
    __tablename__ = "sensor_measurements"

    # "n" : temperature, "u" : "Cel", "v" : 23.5, "t" : 1625247600
    # se salveaza measurement_name = "temperature", unit = "Cel", numeric_value = 23.5
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    mqtt_message_id = Column(
        BigInteger,
        ForeignKey("mqtt_messages.id", ondelete="SET NULL"),
        nullable=True
    )
    # foreign key catre mesajul mqtt original din care a fost extras senML-ul

    topic = Column(String(255), nullable=False)
    source_client_id = Column(String(100), nullable=True)

    base_name = Column(String(255), nullable=True)
    measurement_name = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    numeric_value = Column(Float, nullable=False)

    measured_at = Column(DateTime(timezone=False), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    # pentru a se gasi mai repede inregistrarile
    __table_args__ = (
        Index("idx_sensor_measurements_measurement_time", "measurement_name", "measured_at"),
        Index("idx_sensor_measurements_topic_time", "topic", "measured_at"),
        Index("idx_sensor_measurements_source_time", "source_client_id", "measured_at"),
    )