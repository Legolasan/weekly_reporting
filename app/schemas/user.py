from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserLogin(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserResponse(UserBase):
    id: UUID
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithStats(UserResponse):
    total_weeks: int = 0
    total_items: int = 0
    total_points: int = 0
