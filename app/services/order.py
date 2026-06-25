from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import models
from schemas.order import TransactionCreate


async def create_order(order_data: TransactionCreate, db: AsyncSession):
    result = await db.execute(
        select(models.User).where(models.User.id == order_data.user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    order_result = await db.execute(
        select(models.Order).where(models.Order.reference == order_data.reference)
    )
    db_order = order_result.scalars().first()
    if not db_order:
        order_data_dict = order_data.model_dump()
        order = models.Order(**order_data_dict)

        db.add(order)
        await db.commit()
        await db.refresh(order)
        return db_order
    return {"message": "Transaction already exist"}
