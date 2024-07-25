from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.domain_types import TransactionType
from app.domain_types import ServicePricingType


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    password: Mapped[str]
    tg_id: Mapped[Optional[int]] = mapped_column(index=True, default=None)
    tg_link_token: Mapped[Optional[str]]
    deactivated: Mapped[Optional[bool]]


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    balance: Mapped[Decimal] = mapped_column(default=0)


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    timestamp: Mapped[datetime]
    type: Mapped[TransactionType]
    # amount хранит деньги, такие данные лучше не держать во float
    # А int может оказаться недостаточно гибким
    amount: Mapped[Decimal] = mapped_column(index=True)

    user: Mapped["User"] = relationship()


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[UUID]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    service_name: Mapped[str] = mapped_column(ForeignKey("service.name"))
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transaction.id"))
    start: Mapped[datetime]
    end: Mapped[datetime | None]
    input: Mapped[str | None]
    output: Mapped[str | None]

    user: Mapped["User"] = relationship()
    service: Mapped["Service"] = relationship()
    transaction: Mapped["Transaction"] = relationship()


class Service(Base):
    __tablename__ = "service"

    name: Mapped[str] = mapped_column(primary_key=True)
    description: Mapped[str | None]
    pricing_type: Mapped[ServicePricingType]
    price: Mapped[Decimal]
