from typing import Optional

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.auth.auth_dependency import get_current_user
from app.auth.role_middleware import require_admin, require_authenticated_user
from app.core.config import settings
from app.core.security import verify_device_token
from app.database.db import get_db

security = HTTPBearer(auto_error=False)


async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
):
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if user:
            user["id"] = str(user.pop("_id"))
            user.pop("hashed_password", None)
            return user
    except (JWTError, ValidationError, TypeError):
        return None

    return None


async def get_device_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credentials")

    token = credentials.credentials
    device_id = verify_device_token(token)
    if device_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device credentials")

    return device_id
