from typing import Any, Dict

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.database.db import get_db

security = HTTPBearer()


async def get_current_user(token: HTTPBearer = Depends(security), db=Depends(get_db)) -> Dict[str, Any]:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        payload = jwt.decode(token.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    user_id = payload.get("sub")
    role = payload.get("role")
    email = payload.get("email")
    if not user_id or not role or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims: sub, role, and email are required")

    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    if user.get("role") != role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token role claim does not match active user profile")

    user["id"] = str(user.pop("_id"))
    user.pop("hashed_password", None)
    return user
