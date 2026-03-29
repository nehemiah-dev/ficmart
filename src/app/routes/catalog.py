from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import models
from app.database import get_db
from app.schemas.product import ProductCreate, ProductResponse
from app.schemas.vendor import VendorResponse
from app.utils.auth import get_current_active_vendor

router = APIRouter()


@router.get("", response_model=list[ProductResponse])
async def get_products(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Product)
        .options(selectinload(models.Product.vendor))
        .order_by(models.Product.updated_at.desc())
    )
    products = result.scalars().all()
    return products


@router.get("/{public_id}", response_model=list[ProductResponse])
async def get_product(
    public_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Product)
        .join(models.Product.vendor)
        .options(selectinload(models.Product.vendor))
        .where(models.Vendor.public_id == public_id)
    )
    products = result.scalars().all()
    if not products:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Products not found")
    return products


@router.post("/{public_id}", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    vendor: Annotated[VendorResponse, Depends(get_current_active_vendor)],
):
    if not vendor:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Invalid vendor, please login"
        )
    db_product = models.Product(**product_data.model_dump(), vendor_id=vendor.id)

    db.add(db_product)
    await db.commit()
    await db.refresh(db_product, attribute_names=["vendor"])
    return db_product
