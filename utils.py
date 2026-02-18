from datetime import timedelta, datetime, UTC
from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models
from config import settings
from database import get_db
from schemas import UserResponse, VendorResponse

HASHING_ALGORITHM = settings.hashing_algorithm
JWT_SECRET_KEY = settings.jwt_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token/user"
)  # token comes from /token
password_hash = PasswordHash.recommended()


def get_password_hash(password: str):
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    if len(password) < 8:
        raise ValueError("Password must be atleast 8 characters")

    return password_hash.hash(password)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:

    if not data:
        raise ValueError("Data dictionary cannot be empty")
    data_to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    data_to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(
            data_to_encode, JWT_SECRET_KEY, algorithm=HASHING_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        raise RuntimeError(f"Failed to encode jwt: {str(e)}")


def verify_access_token(token: str):
    """Verify a JWT access token and return the subject (user id) if valid."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[HASHING_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except InvalidTokenError:
        return None
    return payload.get("sub")


async def authenticate_user(
    username: str,
    password: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    user = result.scalars().first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


async def authenticate_vendor(
    username: str,
    password: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Vendor).where(models.Vendor.email == username)
    )
    user = result.scalars().first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_access_token(token)
    if username is None:
        raise credentials_exception

    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    user = result.scalars().first()
    if not user:
        raise credentials_exception
    return user


async def get_current_vendor(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.Vendor:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_access_token(token)
    if username is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=InvalidTokenError)

    result = await db.execute(
        select(models.Vendor).where(models.Vendor.email == username)
    )
    user = result.scalars().first()
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_vendor(
    current_user: Annotated[VendorResponse, Depends(get_current_vendor)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
