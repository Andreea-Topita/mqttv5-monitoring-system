from src.application.security.token_service import create_access_token
from src.application.security.passwords import hash_password, verify_password
from src.domain.entities.user_record import UserRecord
from src.domain.exceptions import (
    InvalidCredentialsError,
    UnauthorizedError,
    UserAlreadyExistsError
)
from src.infrastructure.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register(
        self,
        username: str,
        email: str,
        password: str
    ) -> tuple[UserRecord, str]:
        username = username.strip()
        email = email.strip().lower()

        existing_by_username = self.user_repository.get_by_username(username)
        if existing_by_username is not None:
            raise UserAlreadyExistsError("Username already exists.")

        existing_by_email = self.user_repository.get_by_email(email)
        if existing_by_email is not None:
            raise UserAlreadyExistsError("Email already exists.")

        password_hash = hash_password(password)

        user = self.user_repository.create_user(
            username=username,
            email=email,
            password_hash=password_hash
        )

        access_token = create_access_token(
            user_id=user.id,
            username=user.username
        )

        return user, access_token

    def login(
        self,
        identifier: str,
        password: str
    ) -> tuple[UserRecord, str]:
        identifier = identifier.strip()

        user = self.user_repository.get_by_username_or_email(identifier)

        if user is None:
            raise InvalidCredentialsError("Invalid username/email or password.")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid username/email or password.")

        access_token = create_access_token(
            user_id=user.id,
            username=user.username
        )

        return user, access_token

    def get_current_user(self, user_id: int) -> UserRecord:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise UnauthorizedError("User not found.")

        return user