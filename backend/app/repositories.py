from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserInteraction, UserRating


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).options(selectinload(User.rating_entry)).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, telegram_id: int, referal_id: Optional[int] = None) -> User:
    user = User(telegram_id=telegram_id, referal_id=referal_id)
    session.add(user)

    rating = UserRating(telegram_id=telegram_id, rating=0.0)
    session.add(rating)

    await session.commit()
    result = await session.execute(
        select(User).options(selectinload(User.rating_entry)).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one()


async def update_user_fields(session: AsyncSession, telegram_id: int, **kwargs) -> Optional[User]:
    result = await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(**kwargs).returning(User)
    )
    await session.commit()
    user = result.scalar_one_or_none()
    if user is None:
        return None
    result = await session.execute(
        select(User).options(selectinload(User.rating_entry)).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one()


async def create_interaction(
    session: AsyncSession,
    requester_telegram_id: int,
    responser_telegram_id: int,
    is_like: bool,
) -> UserInteraction:
    interaction = UserInteraction(
        requester_telegram_id=requester_telegram_id,
        responser_telegram_id=responser_telegram_id,
        is_like=is_like,
    )
    session.add(interaction)
    await session.commit()
    await session.refresh(interaction)
    return interaction


async def has_interaction(
    session: AsyncSession,
    requester_telegram_id: int,
    responser_telegram_id: int,
) -> bool:
    result = await session.execute(
        select(UserInteraction).where(
            UserInteraction.requester_telegram_id == requester_telegram_id,
            UserInteraction.responser_telegram_id == responser_telegram_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_user_rating(session: AsyncSession, telegram_id: int) -> float:
    result = await session.execute(
        select(UserRating.rating).where(UserRating.telegram_id == telegram_id)
    )
    rating = result.scalar_one_or_none()
    return rating if rating is not None else 0.0
