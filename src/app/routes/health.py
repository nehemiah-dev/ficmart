from typing import Annotated
from fastapi import APIRouter, Depends
from app.database import get_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("")
async def health(db: Annotated[AsyncSession, Depends(get_db)]):
    status = {"app": "ok"}
    try:
        result = await db.execute(text("SELECT 1"))
        _ = result.scalar()
        status["database"] = "ok"
    except Exception:
        status["database"] = "down"
    return status
