import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# calea catre directorul principal al backend ului 
BASE_DIR = Path(__file__).resolve().parents[3]
# incarcare variabile definite in .env
load_dotenv(BASE_DIR / ".env")

# citire adresa de conectare la baza de date din .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from pc-monitor/.env")

# obiect principal prin care sql alchemy comunica cu baza de date
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# fabrica folosita pentru generarea sesiunilor de baza de date 
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

# clasa mostenita de toate modelele sql alchemy, care contine metadatele tabelelor
Base = declarative_base()