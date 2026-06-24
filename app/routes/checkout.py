from typing import Annotated
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from app.models import models
from app.schemas.user import UserResponse
from app.config import settings
from app.utils.auth import get_current_active_user
from app.utils.reference import generate_transaction_reference

router = APIRouter()


@router.post("")
async def checkout(
    user: Annotated[UserResponse, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = ""
    email = ""
    amount = ""
    channel = [
        "card",
        "bank",
        "apple_pay",
        "ussd",
        "qr",
        "mobile_money",
        "bank_transfer",
        "eft",
        "payattitude",
    ]

    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid user, please login"
        )
    cart = await db.execute(
        select(models.User)
        .join(models.Cart)
        .options(selectinload(models.User.carts))
        .where(models.Cart.user_id == user.id)
    )

    db_cart = cart.scalars().first()
    if not db_cart:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cart not found")

    items = db_cart.carts.items
    user_id = db_cart.id
    name = db_cart.fullname
    email = db_cart.email
    for item in items:
        quantity = item.quantity
        result = await db.execute(
            select(models.Product).where(models.Product.id == item.product_id)
        )
        db_price = result.scalar()
        if not db_price:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Can't find product price"
            )
        else:
            price = db_price.price
            total_amount = (price * quantity) * 100
            amount = int(total_amount)
            # return {"price": total_amount}

    payload = {
        "email": email,
        "amount": amount,
        "channel": channel,
        "reference": generate_transaction_reference(),
        "metadata": {
            "user_id": user_id,
            "name": name,
        },
    }
    headers = {
        "Authorization": f"Bearer {settings.paystack_secret_key.get_secret_value()}",
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=str(f"{settings.paystack_url}/initialize"),
                json=payload,
                headers=headers,
            )
            return response.json()
    except ConnectionError as e:
        return f"Connection error, please try again: {e}"
