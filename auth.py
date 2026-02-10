from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import models
from database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils import authenticate_user, create_access_token, get_password_hash
from schemas import UserCreate, UserResponse

router = APIRouter()


@router.post("/token")
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Users).where(models.Users.username == user.username)
    )
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already exist")
    result = await db.execute(
        select(models.Users).where(models.Users.email == user.email)
    )
    user_email = result.scalars().first()
    if user_email:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already exist")
    if len(user.password) >= 8:
        password_hash = get_password_hash(user.password)
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Password must be atleast 8 characters"
        )

    new_user = models.Users(
        fullname=user.fullname,
        username=user.username,
        email=user.email,
        password=password_hash,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
