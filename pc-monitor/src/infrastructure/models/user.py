from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.sql import func

from src.infrastructure.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)