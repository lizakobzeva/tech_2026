from dataclasses import dataclass
from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models import User, UserInteraction, UserRating


@dataclass
class RatingBreakdown:
    primary_score: float
    behavior_score: float
    referral_bonus: float
    combined_rating: float
    likes: int
    skips: int
    mutual_likes: int
    referrals: int


async def calculate_rating(session: AsyncSession, user: User) -> RatingBreakdown:
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
    filled = sum(1 for value in primary_fields if value is not None and value != "")
    primary_score = (filled / len(primary_fields)) * 100.0

    likes_result = await session.execute(
        select(func.count()).where(
            UserInteraction.responser_telegram_id == user.telegram_id,
            UserInteraction.is_like.is_(True),
        )
    )
    skips_result = await session.execute(
        select(func.count()).where(
            UserInteraction.responser_telegram_id == user.telegram_id,
            UserInteraction.is_like.is_(False),
        )
    )
    likes = likes_result.scalar_one()
    skips = skips_result.scalar_one()
    total_reactions = likes + skips

    like_skip_ratio = (likes / total_reactions) if total_reactions else 0.0

    outgoing_likes_result = await session.execute(
        select(func.count()).where(
            UserInteraction.requester_telegram_id == user.telegram_id,
            UserInteraction.is_like.is_(True),
        )
    )
    outgoing_likes = outgoing_likes_result.scalar_one()

    ui_a = aliased(UserInteraction)
    ui_b = aliased(UserInteraction)
    mutual_likes_result = await session.execute(
        select(func.count()).where(
            ui_a.requester_telegram_id == user.telegram_id,
            ui_a.is_like.is_(True),
            exists(
                select(ui_b.id).where(
                    ui_b.requester_telegram_id == ui_a.responser_telegram_id,
                    ui_b.responser_telegram_id == user.telegram_id,
                    ui_b.is_like.is_(True),
                )
            ),
        )
    )
    mutual_likes = mutual_likes_result.scalar_one()
    mutual_ratio = (mutual_likes / outgoing_likes) if outgoing_likes else 0.0

    activity_factor = 1.0
    if user.last_activity:
        from datetime import datetime

        days_inactive = (datetime.utcnow() - user.last_activity).days
        if days_inactive > 30:
            activity_factor = 0.8
        elif days_inactive > 7:
            activity_factor = 0.9

    behavior_score = (
        (like_skip_ratio * 0.5) + (mutual_ratio * 0.5)
    ) * 100.0 * activity_factor

    referrals_result = await session.execute(
        select(func.count()).where(User.referal_id == user.telegram_id)
    )
    referrals = referrals_result.scalar_one()
    referral_bonus = min(referrals * 5.0, 20.0)

    combined_rating = (primary_score * 0.4) + (behavior_score * 0.5) + referral_bonus

    return RatingBreakdown(
        primary_score=round(primary_score, 2),
        behavior_score=round(behavior_score, 2),
        referral_bonus=round(referral_bonus, 2),
        combined_rating=round(combined_rating, 2),
        likes=likes,
        skips=skips,
        mutual_likes=mutual_likes,
        referrals=referrals,
    )


async def save_user_rating(session: AsyncSession, telegram_id: int, breakdown: RatingBreakdown) -> None:
    result = await session.execute(
        select(UserRating).where(UserRating.telegram_id == telegram_id)
    )
    rating_row = result.scalar_one_or_none()
    if rating_row is None:
        session.add(
            UserRating(telegram_id=telegram_id, rating=breakdown.combined_rating)
        )
    else:
        rating_row.rating = breakdown.combined_rating


async def recalculate_user_rating(session: AsyncSession, telegram_id: int) -> Optional[RatingBreakdown]:
    user_result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return None

    breakdown = await calculate_rating(session, user)
    await save_user_rating(session, telegram_id, breakdown)
    await session.commit()
    return breakdown


async def recalculate_all_ratings(session: AsyncSession) -> int:
    users_result = await session.execute(select(User.telegram_id))
    user_ids = users_result.scalars().all()
    count = 0
    for telegram_id in user_ids:
        if await recalculate_user_rating(session, telegram_id):
            count += 1
    return count
