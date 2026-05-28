from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.security.token_service import decode_access_token
from src.bootstrap.service_container import auth_service
from src.domain.entities.user_record import UserRecord
from src.domain.exceptions import UnauthorizedError


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserRecord:
    if credentials is None:
        raise UnauthorizedError("Authentication token is missing.")

    if credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Invalid authentication scheme.")

    user_id = decode_access_token(credentials.credentials)

    return auth_service.get_current_user(user_id)