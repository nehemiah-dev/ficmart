from typing import Annotated
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm

from app.models import models
from app.database import get_db
from sqlalchemy import select, delete
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
from app.utils.tokens import generate_reset_token
from app.schemas.user import UserCreate, UserResponse
from app.schemas.vendor import VendorCreate, VendorResponse
from app.schemas.password_reset import PasswordResetCreate
from app.services.password_reset import save_reset_details, update_password

from app.workers.mail_workers import send_signup_mail, send_reset_email

router = APIRouter()


@router.post("/login/user")
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


@router.post("/login/vendor")
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


@router.post("/signup/user", response_model=UserResponse, status_code=201)
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
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already exist")
    if len(user.password) < 8:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Password must be atleast 8 characters"
        )
    else:
        password_hash = get_password_hash(user.password)

    new_user = models.User(
        fullname=user.fullname,
        username=user.username,
        email=user.email,
        password_hash=password_hash,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    send_signup_mail.delay(user.email)
    return new_user


@router.post("/signup/vendor", response_model=VendorResponse, status_code=201)
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


@router.post("/forgot-password")
async def forgot_password(email: str, db: Annotated[AsyncSession, Depends(get_db)]):
    if not email:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Please provide your email"
        )
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalars().first()
    if not user:
        return {}
    try:
        token = generate_reset_token()
    except RuntimeError as e:
        return {"message": f"Could not generate token {e}"}
    delta = timedelta(minutes=15)
    now = datetime.now(UTC)
    expires = now + delta
    data = PasswordResetCreate(
        token=token, user_id=user.id, used=False, expires_at=expires
    )
    await save_reset_details(data, db)

    send_reset_email.delay(email, token)
    return {"message": "If the email exists, a reset link has been sent"}


@router.patch("/reset-password")
async def reset_password(
    token: str,
    password: Annotated[str, Form],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not token:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Please provide reset token"
        )
    result = await db.execute(
        select(models.PasswordReset).where(models.PasswordReset.token == token)
    )
    db_token = result.scalars().first()
    if not db_token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Token not found")
    now = datetime.now(UTC)
    expiry = db_token.expires_at
    if expiry <= now:
        await db.execute(
            delete(models.PasswordReset).where(models.PasswordReset.token == token)
        )
        await db.commit()

        return {"message": "Token expired"}
    await update_password(db_token.user_id, password, db)
    await db.execute(
        delete(models.PasswordReset).where(models.PasswordReset.token == token)
    )
    await db.commit()
    await db.refresh(db_token)
    return {"message": "Password reset successful, login with new password"}
