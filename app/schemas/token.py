from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class TokenBase(BaseModel):
    refresh_token: str
    token_type: str = Field(default="bearer")


class TokenCreate(TokenBase):
    pass


class TokenInDB(TokenBase):
    id: int
    user_id: int | None = None
    vendor_id: int | None = None
    is_active: bool
    created_at: datetime
    expires_at: datetime


class TokenResponse(TokenInDB):
    model_config = ConfigDict(from_attributes=True)
