from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from src.database.connection import Base


class ConnectionEvent(Base):
    __tablename__ = "connection_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(String(100), nullable=False)
    broker_address = Column(String(255), nullable=False)
    broker_port = Column(Integer, nullable=False)
    event_type = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)