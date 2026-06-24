from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.password_reset import PasswordResetCreate
from app.models import models
from starlette.responses import JSONResponse
from app.utils.auth import get_password_hash


async def save_reset_details(data: PasswordResetCreate, db: AsyncSession):

    if not data:
        return {}
    data_dict = data.model_dump()
    new_data = models.PasswordReset(**data_dict)

    db.add(new_data)
    await db.commit()
    await db.refresh(new_data)


async def update_password(user_id: int, password: str, db: AsyncSession):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        return JSONResponse(status_code=400, content="User not found")
    user.password_hash = get_password_hash(password)
    # new_password = models.User(password_hash=passwordsh)

    await db.commit()
    await db.refresh(user)
    return JSONResponse(
        status_code=200, content="Succefully updated password, you can now login"
    )
