"""
User data models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr


class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str


class UserInDB(UserBase):
    """User model as stored in database."""
    id: str
    password_hash: str
    created_at: datetime
    created_by: Optional[str] = None


class UserResponse(UserBase):
    """User model for API responses (no password)."""
    id: str
    created_at: datetime


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data encoded in JWT token."""
    user_id: str
    email: str


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str
