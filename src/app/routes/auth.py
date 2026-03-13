from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models import models
from app.database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.auth import (
    authenticate_user,
    authenticate_vendor,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_current_active_user,
    get_current_active_vendor,
)
from app.schemas.user import UserCreate, UserResponse
from app.schemas.vendor import VendorCreate, VendorResponse

router = APIRouter()


@router.post("/user")
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
    refresh_token = create_refresh_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/vendor")
async def login_vendor(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    vendor = await authenticate_vendor(form_data.username, form_data.password, db)
    if not vendor:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": vendor.email})
    refresh_token = create_refresh_token(data={"sub": vendor.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/signup/user", response_model=UserResponse)
async def user_signup(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already exist")
    result = await db.execute(
        select(models.User).where(models.User.email == user.email)
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

    new_user = models.User(
        fullname=user.fullname,
        username=user.username,
        email=user.email,
        password_hash=password_hash,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/signup/vendor", response_model=VendorResponse)
async def vendor_signup(
    vendor: VendorCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.Vendor).where(models.Vendor.store_name == vendor.store_name)
    )
    db_vendor = result.scalars().first()
    if db_vendor:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Store Name already exist")
    result = await db.execute(
        select(models.Vendor).where(models.Vendor.email == vendor.email)
    )
    vendor_email = result.scalars().first()
    if vendor_email:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already exist")
    if len(vendor.password) >= 8:
        password_hash = get_password_hash(vendor.password)
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Password must be atleast 8 characters"
        )

    new_vendor = models.Vendor(
        fullname=vendor.fullname,
        store_name=vendor.store_name,
        email=vendor.email,
        password_hash=password_hash,
    )

    db.add(new_vendor)
    await db.commit()
    await db.refresh(new_vendor)
    return new_vendor


@router.get("/me")
async def read_users_me(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> UserResponse:
    return current_user


@router.get("/vendor")
async def read_vendor(
    current_user: Annotated[VendorResponse, Depends(get_current_active_vendor)],
) -> VendorResponse:
    return current_user
