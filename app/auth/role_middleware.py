from fastapi import Depends, HTTPException, status

from app.auth.auth_dependency import get_current_user


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def require_authenticated_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in {"user", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authentication required")
    return current_user
