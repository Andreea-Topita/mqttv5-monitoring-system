from sqlalchemy import BigInteger, Column, DateTime, String, SmallInteger
from sqlalchemy.sql import func

from src.infrastructure.database.connection import Base


class SubscriptionEvent(Base):
    __tablename__ = "subscription_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    topic = Column(String(255), nullable=False)
    qos = Column(SmallInteger, nullable=False)
    action = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)