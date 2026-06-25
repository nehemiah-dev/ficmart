from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from models import models
from database import get_db
from schemas.user import (
    UserResponse,
)
from schemas.cart import CartItemResponse
from utils.auth import get_current_active_user

router = APIRouter()


@router.post("", response_model=CartItemResponse)
async def add_to_cart(
    user: Annotated[UserResponse, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    product_id: int,
    quantity: int = 1,
):

    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid user, please login"
        )

    result = await db.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Product not found")

    if db_product.stock_quantity < quantity:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Not enough stock")

    db_cart = await db.execute(
        select(models.Cart).where(models.Cart.user_id == user.id, models.Cart.is_active)
    )
    cart = db_cart.scalars().first()
    if not cart:
        cart = models.Cart(user_id=user.id)

        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    result = await db.execute(
        select(models.CartItem).where(
            models.CartItem.cart_id == cart.id, models.CartItem.product_id == product_id
        )
    )

    db_cart_item = result.scalars().first()
    if not db_cart_item:
        cart_item = models.CartItem(
            product_id=product_id, quantity=quantity, cart_id=cart.id
        )
        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)
        return cart_item

    else:
        db_cart_item.quantity += 1
        await db.commit()
        return db_cart_item  # {"message": "Product added to cart"}
