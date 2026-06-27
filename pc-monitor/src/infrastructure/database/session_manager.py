from contextlib import contextmanager

from src.infrastructure.database.connection import SessionLocal

@contextmanager
def session_scope():
    # creeaza o sesiune pentru lucrul cu baza de date
    db = SessionLocal()
    try:
        # executia se opreste temporar si ruleaza add, get, etc
        # cand se iese din context, se reia executia aici
        yield db
        # ofera sesiunea codului din blocul with
        db.commit()
    except Exception:
        # daca apare o exceptie, facem rollback la tranzactie
        db.rollback()
        raise
    finally:
        db.close()