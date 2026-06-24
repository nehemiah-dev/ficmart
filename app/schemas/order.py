from pydantic import BaseModel, EmailStr, Field, ConfigDict
from decimal import Decimal
from datetime import datetime


class TransactionBase(BaseModel):
    user_id: int
    email: EmailStr
    reference: str
    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )


class TransactionCreate(TransactionBase):
    pass


class TransactionInDB(TransactionBase):
    currency: str
    created_at: datetime
    updated_at: datetime


class TransactionResponse(TransactionInDB):
    model_config = ConfigDict(from_attributes=True)
