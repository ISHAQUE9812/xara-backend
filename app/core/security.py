from datetime import timedelta
from typing import Any, Optional, Union

from app.auth.jwt_handler import create_access_token as create_jwt_access_token
from app.auth.jwt_handler import decode_token
from app.auth.password_handler import hash_password as get_password_hash
from app.auth.password_handler import verify_password


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None, role: str = "user", email: str = "", name: str = "") -> str:
    return create_jwt_access_token(
        user_id=str(subject),
        role=role,
        email=email,
        name=name,
        expires_delta=expires_delta,
    )


def verify_token(token: str) -> bool:
    try:
        decode_token(token)
        return True
    except ValueError:
        return False


def verify_device_token(token: str) -> Optional[str]:
    payload = decode_token(token)
    if payload and "device_id" in payload:
        return payload["device_id"]
    return None
