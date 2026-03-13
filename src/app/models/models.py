from __future__ import annotations
from decimal import Decimal
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    Numeric,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.dialects.postgresql import UUID

from uuid import uuid4
from datetime import datetime, UTC
from typing import Optional

from app.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class User(Base, TimestampMixin):
    """User account model."""

    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Use native UUID type for PostgreSQL
    public_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid4,
        index=True,
    )

    fullname: Mapped[str] = mapped_column(String(100), nullable=False)

    username: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,  # Index for lookups
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,  # Index for lookups
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),  # Enough for Argon2
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    carts: Mapped[Cart] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",  # Changed from dynamic to selectin
    )

    tokens: Mapped[list[Token]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"


class Vendor(Base, TimestampMixin):
    """Vendor/store model."""

    __tablename__ = "vendors"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    public_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid4,
        index=True,
    )

    fullname: Mapped[str] = mapped_column(String(100), nullable=False)

    store_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    products: Mapped[list[Product]] = relationship(
        back_populates="vendor",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    tokens: Mapped[list[Token]] = relationship(
        back_populates="vendor",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Vendor(id={self.id}, store_name='{self.store_name}')>"


class Product(Base, TimestampMixin):
    """Product catalog model."""

    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_vendor_created", "vendor_id", "created_at"),
        CheckConstraint("price > 0", name="check_price_positive"),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    vendor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.vendors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,  # For search
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Use Numeric for money - Float has precision issues!
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),  # Max 99,999,999.99
        nullable=False,
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    vendor: Mapped[Vendor] = relationship(back_populates="products")

    cart_items: Mapped[list[CartItem]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"


class Cart(Base, TimestampMixin):
    """Shopping cart model."""

    __tablename__ = "carts"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="carts")

    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",  # Always load items with cart
    )

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user_id={self.user_id}, items={len(self.items)})>"


class CartItem(Base, TimestampMixin):
    """Items in a shopping cart."""

    __tablename__ = "cart_items"

    # Prevent duplicate products in same cart
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    cart_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    # Relationships
    cart: Mapped[Cart] = relationship(back_populates="items")

    product: Mapped[Product] = relationship(back_populates="cart_items")

    def __repr__(self) -> str:
        return f"<CartItem(cart_id={self.cart_id}, product_id={self.product_id}, qty={self.quantity})>"


class Order(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String,
        ForeignKey("public.users.email", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reference: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, default=lambda: str(uuid4())
    )
    currency: Mapped[str] = mapped_column(String(5), nullable=False, default="NGN")


class Token(Base):
    """Token model for refresh tokens"""

    __tablename__ = "tokens"

    __table_args__ = (
        # Token belongs to EITHER user OR vendor, not both
        CheckConstraint(
            "(user_id IS NOT NULL AND vendor_id IS NULL) OR "
            "(user_id IS NULL AND vendor_id IS NOT NULL)",
            name="check_token_owner",
        ),
        Index("ix_tokens_user_active", "user_id", "is_active"),
        Index("ix_tokens_vendor_active", "vendor_id", "is_active"),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Only one should be set
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    vendor_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("public.vendors.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    refresh_token: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
    )

    token_type: Mapped[str] = mapped_column(
        String(20),
        default="Bearer",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional[User]] = relationship(back_populates="tokens")
    vendor: Mapped[Optional[Vendor]] = relationship(back_populates="tokens")

    def __repr__(self) -> str:
        owner = (
            f"user_id={self.user_id}" if self.user_id else f"vendor_id={self.vendor_id}"
        )
        return f"<Token(id={self.id}, {owner}, active={self.is_active})>"
