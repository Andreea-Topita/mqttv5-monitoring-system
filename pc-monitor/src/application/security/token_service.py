import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt as pyjwt
from dotenv import load_dotenv

from src.domain.exceptions import UnauthorizedError


BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from pc-monitor/.env")


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "exp": expire
    }

    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")

        if subject is None:
            raise UnauthorizedError("Invalid authentication token.")

        return int(subject)

    except (pyjwt.InvalidTokenError, ValueError):
        raise UnauthorizedError("Invalid or expired authentication token.")