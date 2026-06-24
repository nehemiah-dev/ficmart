from pydantic import BaseModel, EmailStr, Field, ConfigDict, UUID4
from datetime import datetime


class VendorBase(BaseModel):
    fullname: str = Field(..., min_length=5, max_length=50)
    store_name: str = Field(..., min_length=5, max_length=50)
    email: EmailStr


class VendorCreate(VendorBase):
    password: str = Field(..., min_length=8)


class VendorInDB(VendorBase):
    id: int
    public_id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VendorResponse(VendorInDB):
    model_config = ConfigDict(from_attributes=True)
