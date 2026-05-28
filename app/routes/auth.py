from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.auth_dependency import get_current_user
from app.auth.jwt_handler import create_access_token
from app.auth.password_handler import hash_password, verify_password
from app.auth.role_middleware import require_admin, require_authenticated_user
from app.database.db import get_db
from app.schemas.auth import UserCreate, UserLogin, UserResponse, LoginResponse

router = APIRouter()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db=Depends(get_db)):
    existing = await db["users"].find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_role = user.role.value if hasattr(user.role, "value") else user.role
    now = datetime.now(timezone.utc)
    user_document = {
        "name": user.name,
        "email": user.email,
        "hashed_password": hash_password(user.password),
        "role": user_role,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["users"].insert_one(user_document)
    await db["users"].find_one({"_id": result.inserted_id})

    return {"message": "User created successfully"}


@router.post("/login", response_model=LoginResponse)
async def login(credentials: UserLogin, db=Depends(get_db)):
    user = await db["users"].find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    user_id = str(user["_id"])
    role = user.get("role", "user")
    token = create_access_token(
        user_id=user_id,
        role=role,
        email=user["email"],
        name=user["name"],
    )

    sanitized_user = {
        "id": user_id,
        "name": user["name"],
        "email": user["email"],
        "role": role,
    }
    return {"token": token, "user": sanitized_user}


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/admin/dashboard")
async def admin_dashboard(current_user: dict = Depends(require_admin)):
    return {
        "message": "Admin dashboard access granted",
        "user": current_user,
    }


@router.get("/user/dashboard")
async def user_dashboard(current_user: dict = Depends(require_authenticated_user)):
    return {
        "message": "User dashboard access granted",
        "user": current_user,
    }
