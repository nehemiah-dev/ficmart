from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import models
from app.schemas.order import TransactionCreate


async def create_order(user_id: int, order_data: TransactionCreate, db: AsyncSession):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    order_data_dict = order_data.model_dump()
    order = models.Order(**order_data_dict)

    db.add(order)
    await db.commit()
    await db.refresh(order)
