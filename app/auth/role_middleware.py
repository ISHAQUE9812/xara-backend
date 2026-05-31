import logging
from fastapi import Depends, HTTPException, status

from app.auth.auth_dependency import get_current_user

logger = logging.getLogger(__name__)


async def require_admin(current_user: dict = Depends(get_current_user)):
    logger.info(f"Protected Admin Route Access Attempt - User ID: {current_user.get('id')}, Email: {current_user.get('email')}, Role: {current_user.get('role')}")
    if current_user.get("role") != "admin":
        logger.warning(f"Admin Access Blocked - User ID: {current_user.get('id')}, Email: {current_user.get('email')}, Role: {current_user.get('role')}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    logger.info(f"Admin Access Granted - User ID: {current_user.get('id')}, Email: {current_user.get('email')}")
    return current_user


async def require_authenticated_user(current_user: dict = Depends(get_current_user)):
    logger.info(f"Protected Route Access Attempt - User ID: {current_user.get('id')}, Email: {current_user.get('email')}, Role: {current_user.get('role')}")
    if current_user.get("role") not in {"user", "admin"}:
        logger.warning(f"Access Blocked - User ID: {current_user.get('id')}, Email: {current_user.get('email')}, Role: {current_user.get('role')}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authentication required")
    logger.info(f"Access Granted - User ID: {current_user.get('id')}, Email: {current_user.get('email')}")
    return current_user
