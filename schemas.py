from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class User(BaseModel):
    id: int
    fullname: str = Field(min_length=5, max_length=50)
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)
    created_at: datetime


class UserCreate(BaseModel):
    fullname: str = Field(min_length=5, max_length=50)
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
