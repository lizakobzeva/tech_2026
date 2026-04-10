from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app import repositories
from app.schemas import (
    UserCreate,
    UserResponse,
    UserPartialUpdate,
    InteractionCreate,
    InteractionResponse,
    RatingResponse,
)

router = APIRouter(prefix="/api", tags=["dating"])


@router.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(data: UserCreate, session: AsyncSession = Depends(get_session)):
    existing = await repositories.get_user_by_telegram_id(session, data.telegram_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already registered",
        )

    user = await repositories.create_user(session, data.telegram_id, data.referal_id)
    return _build_user_response(user)


@router.get("/users/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int, session: AsyncSession = Depends(get_session)):
    user = await repositories.get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _build_user_response(user)


@router.patch("/users/{telegram_id}", response_model=UserResponse)
async def update_user(
    telegram_id: int,
    data: UserPartialUpdate,
    session: AsyncSession = Depends(get_session),
):
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    user = await repositories.update_user_fields(session, telegram_id, **update_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _build_user_response(user)


@router.post("/interactions", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(data: InteractionCreate, session: AsyncSession = Depends(get_session)):
    exists = await repositories.has_interaction(
        session, data.requester_telegram_id, data.responser_telegram_id
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Interaction already exists",
        )

    interaction = await repositories.create_interaction(
        session, data.requester_telegram_id, data.responser_telegram_id, data.is_like
    )
    return InteractionResponse(
        id=str(interaction.id),
        requester_telegram_id=interaction.requester_telegram_id,
        responser_telegram_id=interaction.responser_telegram_id,
        is_like=interaction.is_like,
        is_checked=interaction.is_checked,
    )


@router.get("/users/{telegram_id}/rating", response_model=RatingResponse)
async def get_rating(telegram_id: int, session: AsyncSession = Depends(get_session)):
    user = await repositories.get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rating = await repositories.get_user_rating(session, telegram_id)
    return RatingResponse(telegram_id=telegram_id, rating=rating)


def _build_user_response(user) -> UserResponse:
    return UserResponse(
        telegram_id=user.telegram_id,
        age=user.age,
        gender=user.gender,
        interests=user.interests,
        city=user.city,
        age_preferences=user.age_preferences,
        gender_preferences=user.gender_preferences,
        interests_preferences=user.interests_preferences,
        city_preferences=user.city_preferences,
        last_activity=user.last_activity,
        referal_id=user.referal_id,
        is_registered=all([user.age, user.gender, user.interests, user.city]),
        rating=user.rating_entry.rating if user.rating_entry else 0.0,
    )
