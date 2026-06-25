from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models import models


async def delete_cart(user_id: int, db: AsyncSession):
    result = await db.execute(
        select(models.Cart).where(models.Cart.user_id == int(user_id))
    )
    db_cart = result.scalars().first()
    if not db_cart:
        return {"message": "Cart not found"}
    result = await db.execute(
        delete(models.Cart).where(models.Cart.user_id == int(db_cart.user_id))
    )
    await db.commit()
    await db.refresh(db_cart)
    return {}
