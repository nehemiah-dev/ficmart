from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=20, max_length=500)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    stock_quantity: int = Field(gt=0)


class ProductCreate(ProductBase):
    pass


class ProductInDB(ProductBase):
    id: int
    vendor_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductResponse(ProductInDB):
    model_config = ConfigDict(from_attributes=True)
