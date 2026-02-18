from pydantic import BaseModel, EmailStr, Field, ConfigDict
from decimal import Decimal
from datetime import datetime


class UserBase(BaseModel):
    fullname: str = Field(..., min_length=5, max_length=50)
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserInDB(UserBase):
    id: int
    public_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserResponse(UserInDB):
    model_config = ConfigDict(from_attributes=True)


class VendorBase(BaseModel):
    fullname: str = Field(..., min_length=5, max_length=50)
    store_name: str = Field(..., min_length=5, max_length=50)
    email: EmailStr


class VendorCreate(VendorBase):
    password: str = Field(..., min_length=8)


class VendorInDB(VendorBase):
    id: int
    public_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VendorResponse(VendorInDB):
    model_config = ConfigDict(from_attributes=True)


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
    vendor: VendorResponse
    created_at: datetime
    updated_at: datetime


class ProductResponse(ProductInDB):
    model_config = ConfigDict(from_attributes=True)


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


class TransactionBase(BaseModel):
    user_id: UserResponse
    email: UserResponse
    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )
    reference: str
    currency: str
    callback_url: str


class TransactionCreate(TransactionBase):
    pass


class TransactionInDB(TransactionBase):
    created_at: datetime
    updated_at: datetime


class TransactionResponse(TransactionInDB):
    model_config = ConfigDict(from_attributes=True)


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
