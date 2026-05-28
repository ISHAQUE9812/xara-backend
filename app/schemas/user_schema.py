from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


# ============ ROLE ENUM ============

class UserRole(str, Enum):
    admin = "admin"
    user = "user"


# ============ USER SCHEMAS ============

class UserSignup(BaseModel):
    """Schema for user signup (matches frontend payload with 'name' field)."""
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, max_length=128, description="User's password (min 6 chars)")
    role: UserRole = Field(default=UserRole.user, description="User role: admin or user")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Full name cannot be empty or whitespace")
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Ensure password meets requirements."""
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class UserCreate(BaseModel):
    """Schema for user registration (backward compatibility)."""
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
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
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    role: str = Field(..., description="User role")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """Internal user model with hashed password (never exposed via API)."""
    hashed_password: str


# ============ TOKEN SCHEMAS ============

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user details")


class TokenData(BaseModel):
    """Schema for decoded JWT token payload."""
    user_id: Optional[str] = Field(None, description="User ID from token sub claim")

    model_config = ConfigDict(from_attributes=True)
