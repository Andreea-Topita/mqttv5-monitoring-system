from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.sql import func

from src.infrastructure.database.connection import Base

# pastreaza utilizatorii aplicatiei 
class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True) # unqiue ca sa nu am 2 conturi cu acelasi username sau email
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    # baza de date completeaza automat data curenta la inserare