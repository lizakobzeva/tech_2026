from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserInteraction, UserRating
from app.rating_service import RatingBreakdown, calculate_rating, recalculate_user_rating


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
    created_user = result.scalar_one()
    await recalculate_user_rating(session, telegram_id)
    if referal_id is not None:
        await recalculate_user_rating(session, referal_id)
    result = await session.execute(
        select(User).options(selectinload(User.rating_entry)).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one()


async def update_user_fields(session: AsyncSession, telegram_id: int, **kwargs) -> Optional[User]:
    kwargs["last_activity"] = datetime.utcnow()
    result = await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(**kwargs).returning(User)
    )
    await session.commit()
    user = result.scalar_one_or_none()
    if user is None:
        return None
    await recalculate_user_rating(session, telegram_id)
    result = await session.execute(
        select(User).options(selectinload(User.rating_entry)).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one()


async def create_interaction(
    session: AsyncSession,
    requester_telegram_id: int,
    responser_telegram_id: int,
    is_like: bool,
) -> tuple[UserInteraction, bool]:
    interaction = UserInteraction(
        requester_telegram_id=requester_telegram_id,
        responser_telegram_id=responser_telegram_id,
        is_like=is_like,
    )
    session.add(interaction)

    await session.execute(
        update(User)
        .where(User.telegram_id == requester_telegram_id)
        .values(last_activity=datetime.utcnow())
    )

    await session.commit()
    await session.refresh(interaction)

    is_match = False
    if is_like:
        is_match = await has_mutual_like(session, requester_telegram_id, responser_telegram_id)

    await recalculate_user_rating(session, responser_telegram_id)
    await recalculate_user_rating(session, requester_telegram_id)

    return interaction, is_match


async def has_mutual_like(
    session: AsyncSession,
    requester_telegram_id: int,
    responser_telegram_id: int,
) -> bool:
    result = await session.execute(
        select(UserInteraction).where(
            UserInteraction.requester_telegram_id == responser_telegram_id,
            UserInteraction.responser_telegram_id == requester_telegram_id,
            UserInteraction.is_like.is_(True),
        )
    )
    return result.scalar_one_or_none() is not None


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


async def get_rating_breakdown(session: AsyncSession, telegram_id: int) -> Optional[RatingBreakdown]:
    user_result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return None
    return await calculate_rating(session, user)


def _split_interests(value: Optional[str]) -> set[str]:
    if not value:
        return set()
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _matches_preferences(requester: User, candidate: User) -> bool:
    if requester.age_preferences is not None and (
        candidate.age is None or candidate.age > requester.age_preferences
    ):
        return False

    if (
        requester.gender_preferences
        and requester.gender_preferences != "all"
        and candidate.gender != requester.gender_preferences
    ):
        return False

    if requester.city_preferences and (
        candidate.city is None
        or candidate.city.strip().lower() != requester.city_preferences.strip().lower()
    ):
        return False

    wanted_interests = _split_interests(requester.interests_preferences)
    if wanted_interests:
        candidate_interests = _split_interests(candidate.interests)
        if not wanted_interests.intersection(candidate_interests):
            return False

    return True


async def get_next_candidate(session: AsyncSession, requester_telegram_id: int) -> Optional[User]:
    requester = await get_user_by_telegram_id(session, requester_telegram_id)
    if requester is None:
        return None

    interacted_result = await session.execute(
        select(UserInteraction.responser_telegram_id).where(
            UserInteraction.requester_telegram_id == requester_telegram_id
        )
    )
    interacted_ids = set(interacted_result.scalars().all())

    users_result = await session.execute(
        select(User)
        .options(selectinload(User.rating_entry))
        .where(User.telegram_id != requester_telegram_id)
    )
    candidates = users_result.scalars().all()

    available_candidates = []
    for candidate in candidates:
        if candidate.telegram_id in interacted_ids:
            continue
        if not all([candidate.age, candidate.gender, candidate.interests, candidate.city]):
            continue
        if not _matches_preferences(requester, candidate):
            continue
        available_candidates.append(candidate)

    available_candidates.sort(
        key=lambda user: (
            user.rating_entry.rating if user.rating_entry else 0.0,
            user.last_activity,
        ),
        reverse=True,
    )
    return available_candidates[0] if available_candidates else None
