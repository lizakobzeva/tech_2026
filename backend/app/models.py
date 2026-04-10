from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    BIGINT,
    BOOLEAN,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    interests: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    age_preferences: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender_preferences: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    interests_preferences: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city_preferences: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    referal_id: Mapped[Optional[int]] = mapped_column(
        BIGINT, ForeignKey("users.telegram_id"), nullable=True
    )

    rating_entry: Mapped[Optional["UserRating"]] = relationship(
        "UserRating", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sent_interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction",
        foreign_keys="UserInteraction.requester_telegram_id",
        back_populates="requester",
    )
    received_interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction",
        foreign_keys="UserInteraction.responser_telegram_id",
        back_populates="responser",
    )


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid4())
    )
    requester_telegram_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("users.telegram_id")
    )
    responser_telegram_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("users.telegram_id")
    )
    is_like: Mapped[bool] = mapped_column(BOOLEAN)
    is_checked: Mapped[Optional[bool]] = mapped_column(BOOLEAN, nullable=True)

    __table_args__ = (
        UniqueConstraint("requester_telegram_id", "responser_telegram_id"),
    )

    requester: Mapped["User"] = relationship(
        "User", foreign_keys=[requester_telegram_id], back_populates="sent_interactions"
    )
    responser: Mapped["User"] = relationship(
        "User", foreign_keys=[responser_telegram_id], back_populates="received_interactions"
    )


class UserRating(Base):
    __tablename__ = "user_ratings"

    telegram_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("users.telegram_id"), primary_key=True
    )
    rating: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped["User"] = relationship("User", back_populates="rating_entry")
