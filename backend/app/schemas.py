from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    telegram_id: int
    referal_id: Optional[int] = None


class UserResponse(BaseModel):
    telegram_id: int
    age: Optional[int] = None
    gender: Optional[str] = None
    interests: Optional[str] = None
    city: Optional[str] = None
    age_preferences: Optional[int] = None
    gender_preferences: Optional[str] = None
    interests_preferences: Optional[str] = None
    city_preferences: Optional[str] = None
    last_activity: datetime
    referal_id: Optional[int] = None
    is_registered: bool = True
    rating: float = 0.0


class UserPartialUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    interests: Optional[str] = None
    city: Optional[str] = None
    age_preferences: Optional[int] = None
    gender_preferences: Optional[str] = None
    interests_preferences: Optional[str] = None
    city_preferences: Optional[str] = None


class InteractionCreate(BaseModel):
    requester_telegram_id: int
    responser_telegram_id: int
    is_like: bool


class InteractionResponse(BaseModel):
    id: str
    requester_telegram_id: int
    responser_telegram_id: int
    is_like: bool
    is_checked: Optional[bool] = None


class RatingResponse(BaseModel):
    telegram_id: int
    rating: float
