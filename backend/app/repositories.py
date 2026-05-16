from typing import Optional

from sqlalchemy import exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

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
    created_user = result.scalar_one()
    await _recalculate_user_rating(session, telegram_id)
    if referal_id is not None:
        await _recalculate_user_rating(session, referal_id)
    return created_user


async def update_user_fields(session: AsyncSession, telegram_id: int, **kwargs) -> Optional[User]:
    result = await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(**kwargs).returning(User)
    )
    await session.commit()
    user = result.scalar_one_or_none()
    if user is None:
        return None
    await _recalculate_user_rating(session, telegram_id)
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
    await _recalculate_user_rating(session, responser_telegram_id)
    await _recalculate_user_rating(session, requester_telegram_id)
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


async def _recalculate_user_rating(session: AsyncSession, telegram_id: int) -> None:
    user_result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        return

    # Уровень 1: первичный рейтинг на основе заполненности анкеты.
    primary_fields = [
        user.age,
        user.gender,
        user.interests,
        user.city,
        user.age_preferences,
        user.gender_preferences,
        user.interests_preferences,
        user.city_preferences,
    ]
    filled_primary_fields = sum(1 for value in primary_fields if value is not None and value != "")
    primary_score = (filled_primary_fields / len(primary_fields)) * 100.0

    # Уровень 2: поведенческий рейтинг.
    likes_result = await session.execute(
        select(func.count()).where(
            UserInteraction.responser_telegram_id == telegram_id,
            UserInteraction.is_like.is_(True),
        )
    )
    dislikes_result = await session.execute(
        select(func.count()).where(
            UserInteraction.responser_telegram_id == telegram_id,
            UserInteraction.is_like.is_(False),
        )
    )

    likes = likes_result.scalar_one()
    dislikes = dislikes_result.scalar_one()
    total = likes + dislikes

    approval_ratio = (likes / total) if total else 0.0

    outgoing_likes_result = await session.execute(
        select(func.count()).where(
            UserInteraction.requester_telegram_id == telegram_id,
            UserInteraction.is_like.is_(True),
        )
    )
    outgoing_likes = outgoing_likes_result.scalar_one()

    ui_a = aliased(UserInteraction)
    ui_b = aliased(UserInteraction)
    mutual_likes_result = await session.execute(
        select(func.count()).where(
            ui_a.requester_telegram_id == telegram_id,
            ui_a.is_like.is_(True),
            exists(
                select(ui_b.id).where(
                    ui_b.requester_telegram_id == ui_a.responser_telegram_id,
                    ui_b.responser_telegram_id == telegram_id,
                    ui_b.is_like.is_(True),
                )
            ),
        )
    )
    mutual_likes = mutual_likes_result.scalar_one()
    mutual_ratio = (mutual_likes / outgoing_likes) if outgoing_likes else 0.0

    behavior_score = ((approval_ratio * 0.7) + (mutual_ratio * 0.3)) * 100.0

    # Уровень 3: комбинированный рейтинг + реферальный фактор.
    referrals_result = await session.execute(
        select(func.count()).where(User.referal_id == telegram_id)
    )
    referral_count = referrals_result.scalar_one()
    referral_bonus = min(referral_count * 5.0, 20.0)

    combined_rating = (primary_score * 0.4) + (behavior_score * 0.5) + referral_bonus

    exists_result = await session.execute(
        select(UserRating).where(UserRating.telegram_id == telegram_id)
    )
    rating_row = exists_result.scalar_one_or_none()
    if rating_row is None:
        session.add(UserRating(telegram_id=telegram_id, rating=round(combined_rating, 2)))
    else:
        rating_row.rating = round(combined_rating, 2)

    await session.commit()


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
