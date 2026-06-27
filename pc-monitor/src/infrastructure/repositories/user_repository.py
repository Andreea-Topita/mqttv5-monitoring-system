from typing import Optional

from sqlalchemy import or_, select

from src.domain.entities.user_record import UserRecord
from src.infrastructure.database.session_manager import session_scope
from src.infrastructure.mappers.user_mapper import to_user_record
from src.infrastructure.models.user import User


class UserRepository:
    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str
    ) -> UserRecord:
        # deschidere sesiune si tranzactie
        with session_scope() as db:
            # creare obiect sql alchemy user
            item = User(
                username=username,
                email=email,
                password_hash=password_hash
            )

            # insert in baza de date
            db.add(item)
            db.flush() # trimite insert catre bd
            db.refresh(item) # citeste valorile generate de bd, adica id si created_at

            # returneaza obiectul salvat ca un UserRecord
            return to_user_record(item)

    def get_by_id(self, user_id: int) -> Optional[UserRecord]:
        with session_scope() as db:
            stmt = select(User).where(User.id == user_id)
            item = db.execute(stmt).scalar_one_or_none() # un singur obiect user sau none daca nu exista

            if item is None:
                return None

            return to_user_record(item)

    def get_by_username(self, username: str) -> Optional[UserRecord]:
        with session_scope() as db:
            stmt = select(User).where(User.username == username)
            item = db.execute(stmt).scalar_one_or_none()

            if item is None:
                return None

            return to_user_record(item)

    def get_by_email(self, email: str) -> Optional[UserRecord]:
        with session_scope() as db:
            stmt = select(User).where(User.email == email)
            item = db.execute(stmt).scalar_one_or_none()

            if item is None:
                return None

            return to_user_record(item)

    def get_by_username_or_email(self, identifier: str) -> Optional[UserRecord]:
        with session_scope() as db:
            stmt = select(User).where(
                or_(
                    User.username == identifier,
                    User.email == identifier
                )
            )

            item = db.execute(stmt).scalar_one_or_none()

            if item is None:
                return None

            return to_user_record(item)