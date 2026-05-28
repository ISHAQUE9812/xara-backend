from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user_schema import UserCreate, UserSignup, UserLogin, UserResponse, Token
from app.models.user_model import UserModel
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.utils.deps import get_current_user
from datetime import timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ REGISTER ============

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
@router.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(user: UserCreate, db=Depends(get_db)):
    """
    Register a new user account (expects full_name field).
    
    - Validates email uniqueness
    - Hashes password with bcrypt
    - Assigns role (default: user)
    - Returns user object (no password)
    """
    # Check if email already exists
    existing_user = await db["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )
    
    # Build user document with hashed password
    user_data = user.model_dump()
    hashed_password = get_password_hash(user_data.pop("password"))
    user_data["hashed_password"] = hashed_password

    document = UserModel.create_document(user_data)
    result = await db["users"].insert_one(document)
    
    # Fetch and return the created user
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    formatted = UserModel.format_response(created_user)
    
    logger.info(f"New user registered: {formatted.get('email')} (role: {formatted.get('role')})")
    return formatted


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
@router.post("/signup/", response_model=Token, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def signup(user: UserSignup, db=Depends(get_db)):
    """
    Signup endpoint for new user registration (expects name field from frontend).
    
    - Accepts 'name' field (from frontend SignupForm)
    - Maps 'name' to 'full_name' for storage
    - Validates email uniqueness
    - Hashes password with bcrypt
    - Assigns role (default: user)
    - Returns JWT token immediately so user is logged in after signup
    """
    # Check if email already exists
    existing_user = await db["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )
    
    # Build user document with hashed password
    user_data = user.model_dump()
    # Map 'name' to 'full_name' for consistency with database schema
    user_data["full_name"] = user_data.pop("name")
    hashed_password = get_password_hash(user_data.pop("password"))
    user_data["hashed_password"] = hashed_password

    document = UserModel.create_document(user_data)
    result = await db["users"].insert_one(document)
    
    # Fetch the created user
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    formatted_user = UserModel.format_response(created_user)
    
    # Generate JWT token for immediate login
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(created_user["_id"]),
        expires_delta=access_token_expires
    )
    
    logger.info(f"New user signed up: {formatted_user.get('email')} (role: {formatted_user.get('role')})")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": formatted_user
    }


# ============ LOGIN ============

@router.post("/login", response_model=Token, tags=["Authentication"])
@router.post("/login/", response_model=Token, tags=["Authentication"])
async def login(user_data: UserLogin, db=Depends(get_db)):
    """
    Authenticate user and return JWT access token with user details.
    
    - Validates email exists
    - Verifies password against bcrypt hash
    - Generates JWT token with user_id as subject
    - Returns token + full user object
    """
    # Find user by email
    user = await db["users"].find_one({"email": user_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact administrator."
        )
    
    # Generate JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user["_id"]),
        expires_delta=access_token_expires
    )
    
    # Format user response (strips _id and hashed_password)
    user_response = UserModel.format_response(user)
    
    logger.info(f"User logged in: {user_response.get('email')}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }


# ============ CURRENT USER ============

@router.get("/me", response_model=UserResponse, tags=["Authentication"])
@router.get("/me/", response_model=UserResponse, tags=["Authentication"])
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get the currently authenticated user's profile.
    
    Requires valid JWT Bearer token in Authorization header.
    """
    return current_user
