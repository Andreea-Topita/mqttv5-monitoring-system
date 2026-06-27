from sqlalchemy import BigInteger, Column, DateTime, Text, TIMESTAMP, String, SmallInteger
from sqlalchemy.sql import func

from src.infrastructure.database.connection import Base

# pastreaza mesajele mqtt in forma originala
class MQTTMessage(Base):
    __tablename__ = "mqtt_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    topic = Column(String(255), nullable=False)
    payload = Column(Text, nullable=False) # continut original { "bn": "pico", ...}
    qos = Column(SmallInteger, nullable=False)
    direction = Column(String(20), nullable=False) # inbound adica de la broker 
                                                    # sau outbound adica catre broker
    source_client_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)