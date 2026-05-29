from src.api.schemas.auth import AuthResponse, UserResponse
from src.domain.entities.user_record import UserRecord


def to_auth_response(
    user: UserRecord,
    access_token: str
) -> AuthResponse:
    return AuthResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


def to_user_response(user: UserRecord) -> UserResponse:
    return UserResponse.model_validate(user)