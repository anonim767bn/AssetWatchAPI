"""This module contains the SQLAlchemy ORM models for the application."""

from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Text,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


class UUIDmixin:
    """Mixin class for models that use a UUID as primary key."""

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)


class User(Base, UUIDmixin):
    """User model."""

    __tablename__ = 'user'

    username: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True)
    hash_password: Mapped[str] = mapped_column(Text, nullable=False)

    assets: Mapped[List['Asset']] = relationship('Asset', back_populates='user')

    __table_args__ = (
        CheckConstraint('LENGTH(username) < 50'),
    )


class Asset(Base, UUIDmixin):
    """Asset model."""

    __tablename__ = 'asset'

    amount_price_histories: Mapped[List['AssetAmountPriceHistory']] = relationship(
        'AssetAmountPriceHistory', back_populates='asset')
    currency_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey('currency.id'), index=True, nullable=False)
    currency: Mapped['Currency'] = relationship(
        'Currency', back_populates='assets')

    user_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey('user.id'), index=True, nullable=False)
    user: Mapped['User'] = relationship(
        'User', back_populates='assets')
    __table_args__ = (
        UniqueConstraint('user_id', 'currency_id'),
    )


class AssetAmountPriceHistory(Base, UUIDmixin):
    """AssetAmountPriceHistory model."""

    __tablename__ = 'asset_price_history'

    amount: Mapped[float]
    asset_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey('asset.id'), index=True, nullable=False)
    asset: Mapped['Asset'] = relationship(
        'Asset', back_populates='amount_price_histories')
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False)
    price: Mapped[float]

    __table_args__ = (
        UniqueConstraint('asset_id', 'timestamp'),
        CheckConstraint('price >= 0'),
        CheckConstraint('amount >= 0'),
    )


class Currency(Base, UUIDmixin):
    """Currency model."""

    __tablename__ = 'currency'

    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    assets: Mapped[List['Asset']] = relationship(
        'Asset', back_populates='currency')
    price_histories: Mapped[List['PriceHistory']] = relationship(
        'PriceHistory', back_populates='currency')

    __table_args__ = (
        UniqueConstraint('name', 'symbol'),
        CheckConstraint('symbol = upper(symbol)'),
        CheckConstraint('LENGTH(name) < 50'),
    )


class PriceHistory(Base, UUIDmixin):
    """PriceHistory model."""

    __tablename__ = 'price_history'

    currency_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey('currency.id'), index=True)
    currency: Mapped['Currency'] = relationship(
        'Currency', back_populates='price_histories')
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False)
    price: Mapped[float]

    __table_args__ = (
        UniqueConstraint('currency_id', 'timestamp'),
        CheckConstraint('price >= 0'),
    )
