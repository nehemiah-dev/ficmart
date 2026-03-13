from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CartBase(BaseModel):
    pass


class CartCreate(CartBase):
    pass


class CartInDB(CartBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CartResponse(CartInDB):
    model_config = ConfigDict(from_attributes=True)


class CartItemBase(BaseModel):
    product_id: int
    quantity: int


class CartItemCreate(CartItemBase):
    pass


class CartItemInDB(CartItemBase):
    id: int
    cart_id: int
    created_at: datetime
    updated_at: datetime


class CartItemResponse(CartItemInDB):
    model_config = ConfigDict(from_attributes=True)
