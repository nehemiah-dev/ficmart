from pydantic import BaseModel
from datetime import datetime


class PasswordResetBase(BaseModel):
    user_id: int
    token: str
    used: bool
    expires_at: datetime


class PasswordResetCreate(PasswordResetBase):
    pass


class PasswordResetInDb(PasswordResetBase):
    id: int
    created_at: datetime
