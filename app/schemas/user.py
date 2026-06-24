from pydantic import BaseModel, EmailStr, Field, ConfigDict, UUID4
from datetime import datetime


class UserBase(BaseModel):
    fullname: str = Field(..., min_length=5, max_length=50)
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserInDB(UserBase):
    id: int
    public_id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserResponse(UserInDB):
    model_config = ConfigDict(from_attributes=True)
