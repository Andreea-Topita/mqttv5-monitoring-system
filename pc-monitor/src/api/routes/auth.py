from fastapi import APIRouter, Depends

from src.api.dependencies.auth import get_current_user
from src.api.mappers.auth_mapper import to_auth_response, to_user_response
from src.api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse
)
from src.bootstrap.service_container import auth_service
from src.domain.entities.user_record import UserRecord


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    user, access_token = auth_service.register(
        username=payload.username,
        email=str(payload.email),
        password=payload.password
    )

    return to_auth_response(user, access_token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    user, access_token = auth_service.login(
        identifier=payload.identifier,
        password=payload.password
    )

    return to_auth_response(user, access_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserRecord = Depends(get_current_user)):
    return to_user_response(current_user)