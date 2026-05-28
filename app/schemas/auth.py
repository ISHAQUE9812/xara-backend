from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

# ============ ROLE ENUM ============
class UserRole(str, Enum):
    admin = "admin"
    user = "user"

# ============ USER SCHEMAS ============
class UserCreate(BaseModel):
    """Schema for user registration.
    Accepts a simple name instead of full_name.
    """
    name: str = Field(..., min_length=2, max_length=100, description="User's name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, max_length=128, description="User's password (min 6 chars)")
    role: UserRole = Field(default=UserRole.user, description="User role: admin or user")

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")

class UserResponse(BaseModel):
    """Schema for user data in API responses (no sensitive fields)."""
    id: str = Field(..., description="User's unique identifier")
    name: str = Field(..., description="User's name")
    email: str = Field(..., description="User's email address")
    role: str = Field(..., description="User role")

    model_config = ConfigDict(from_attributes=True)

class UserInDB(UserResponse):
    """Internal user model with hashed password (never exposed via API)."""
    hashed_password: str

# ============ TOKEN SCHEMAS ============
class Token(BaseModel):
    """Schema for JWT token response (used for login)."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    role: str = Field(..., description="User role")
    user_id: str = Field(..., description="User identifier")


class LoginResponse(BaseModel):
    token: str = Field(..., description="JWT access token")
    user: UserResponse = Field(..., description="Authenticated user details")


class SignupResponse(BaseModel):
    """Schema for signup success response."""
    message: str = Field(..., description="Human readable message")

class TokenData(BaseModel):
    """Schema for decoded JWT token payload."""
    user_id: Optional[str] = Field(None, description="User ID from token sub claim")
    role: Optional[str] = Field(None, description="User role from token claim")

    model_config = ConfigDict(from_attributes=True)
