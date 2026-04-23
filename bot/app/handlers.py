import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from app.states import RegistrationStates, SearchStates
from app.keyboards import (
    get_start_keyboard,
    get_gender_keyboard,
    get_gender_preference_keyboard,
    get_main_menu_keyboard,
    get_like_dislike_keyboard,
)
from app.http_requests import backend_client

logger = logging.getLogger(__name__)

router = Router(name="handlers")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    try:
        user = await backend_client.register_user(telegram_id)
    except Exception as e:
        logger.error("Failed to register user %d: %s", telegram_id, e)
        await message.answer("Произошла ошибка. Попробуйте позже.")
        return

    await state.clear()

    if user.get("is_registered"):
        await message.answer(
            f"С возвращением, {message.from_user.first_name}!",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await state.set_state(RegistrationStates.waiting_for_start)
        await message.answer(
            f"Привет, {message.from_user.first_name}! Давай заполним анкету.",
            reply_markup=get_start_keyboard(),
        )


@router.message(F.text == "Начать регистрацию")
async def start_registration(message: Message, state: FSMContext):
    try:
        user = await backend_client.get_user(message.from_user.id)
    except Exception as e:
        logger.error("Failed to get user %d before registration: %s", message.from_user.id, e)
        await message.answer("Произошла ошибка. Попробуйте позже.")
        return

    if user.get("is_registered"):
        await state.clear()
        await message.answer(
            "Анкета уже заполнена. Используй меню ниже.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await state.set_state(RegistrationStates.waiting_for_age)
    await message.answer("Сколько тебе лет? (введи число)")


@router.message(RegistrationStates.waiting_for_age, F.text.regexp(r"^\d{1,3}$"))
async def process_age(message: Message, state: FSMContext):
    age = int(message.text)
    if age < 14 or age > 120:
        await message.answer("Укажи реальный возраст (от 14 до 120)")
        return

    await state.update_data(age=age)
    await state.set_state(RegistrationStates.waiting_for_gender)
    await message.answer("Укажи свой пол:", reply_markup=get_gender_keyboard())


@router.message(RegistrationStates.waiting_for_age)
async def invalid_age(message: Message):
    await message.answer("Введи число (например: 25)")


@router.callback_query(F.data.startswith("gender:"), RegistrationStates.waiting_for_gender)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":")[1]
    gender_map = {"male": "male", "female": "female", "other": "other"}
    await state.update_data(gender=gender_map.get(gender, gender))
    await state.set_state(RegistrationStates.waiting_for_interests)
    await callback.message.edit_text("Расскажи о своих интересах (через запятую):")
    await callback.answer()


@router.message(RegistrationStates.waiting_for_interests, F.text.len() >= 2)
async def process_interests(message: Message, state: FSMContext):
    await state.update_data(interests=message.text.strip())
    await state.set_state(RegistrationStates.waiting_for_city)
    await message.answer("В каком ты городе?")


@router.message(RegistrationStates.waiting_for_interests)
async def invalid_interests(message: Message):
    await message.answer("Напиши хотя бы пару слов о своих интересах")


@router.message(RegistrationStates.waiting_for_city, F.text.len() >= 2)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=city)

    data = await state.get_data()
    try:
        await backend_client.update_user(
            message.from_user.id,
            age=data.get("age"),
            gender=data.get("gender"),
            interests=data.get("interests"),
            city=city,
        )
    except Exception as e:
        logger.error("Failed to update user %d: %s", message.from_user.id, e)
        await message.answer("Ошибка сохранения. Попробуй позже.")
        await state.clear()
        return

    await state.set_state(RegistrationStates.waiting_for_age_preference)
    await message.answer("Какой максимальный возраст ты ищешь? (введи число)")


@router.message(RegistrationStates.waiting_for_city)
async def invalid_city(message: Message):
    await message.answer("Введи название города")


@router.message(RegistrationStates.waiting_for_age_preference, F.text.regexp(r"^\d{1,3}$"))
async def process_age_preference(message: Message, state: FSMContext):
    age_pref = int(message.text)
    if age_pref < 14 or age_pref > 120:
        await message.answer("Укажи реальный возраст (от 14 до 120)")
        return

    await state.update_data(age_preferences=age_pref)
    await state.set_state(RegistrationStates.waiting_for_gender_preference)
    await message.answer(
        "Кого ты ищешь?", reply_markup=get_gender_preference_keyboard()
    )


@router.message(RegistrationStates.waiting_for_age_preference)
async def invalid_age_pref(message: Message):
    await message.answer("Введи число (например: 35)")


@router.callback_query(
    F.data.startswith("gender_pref:"), RegistrationStates.waiting_for_gender_preference
)
async def process_gender_preference(callback: CallbackQuery, state: FSMContext):
    pref = callback.data.split(":")[1]
    await state.update_data(gender_preferences=pref)
    await state.set_state(RegistrationStates.waiting_for_interests_preference)
    await callback.message.edit_text(
        "Какие интересы ты ищешь в партнёре? (через запятую)"
    )
    await callback.answer()


@router.message(RegistrationStates.waiting_for_interests_preference, F.text.len() >= 2)
async def process_interests_preference(message: Message, state: FSMContext):
    await state.update_data(interests_preferences=message.text.strip())
    await state.set_state(RegistrationStates.waiting_for_city_preference)
    await message.answer("В каком городе ты ищешь партнёра?")


@router.message(RegistrationStates.waiting_for_interests_preference)
async def invalid_interests_pref(message: Message):
    await message.answer("Напиши хотя бы пару слов")


@router.message(RegistrationStates.waiting_for_city_preference, F.text.len() >= 2)
async def process_city_preference(message: Message, state: FSMContext):
    city_pref = message.text.strip()
    await state.update_data(city_preferences=city_pref)

    data = await state.get_data()
    try:
        await backend_client.update_user(
            message.from_user.id,
            age_preferences=data.get("age_preferences"),
            gender_preferences=data.get("gender_preferences"),
            interests_preferences=data.get("interests_preferences"),
            city_preferences=city_pref,
        )
    except Exception as e:
        logger.error("Failed to update preferences for user %d: %s", message.from_user.id, e)

    await state.clear()
    await message.answer(
        "Регистрация завершена! Теперь ты можешь искать пару.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(RegistrationStates.waiting_for_city_preference)
async def invalid_city_pref(message: Message):
    await message.answer("Введи название города")


@router.message(F.text == "Мой профиль")
async def show_profile(message: Message):
    try:
        user = await backend_client.get_user(message.from_user.id)
        rating_value = user.get("rating")
        if rating_value is None:
            rating_value = 0.0
        profile_text = (
            f"Твой профиль\n\n"
            f"Возраст: {user.get('age', '—')}\n"
            f"Пол: {user.get('gender', '—')}\n"
            f"Интересы: {user.get('interests', '—')}\n"
            f"Город: {user.get('city', '—')}\n"
            f"Рейтинг: {float(rating_value):.2f}\n"
        )
        await message.answer(profile_text)
    except Exception as e:
        logger.error("Failed to fetch profile for %d: %s", message.from_user.id, e)
        await message.answer("Не удалось загрузить профиль")


@router.message(F.text == "Мой рейтинг")
async def show_rating(message: Message):
    try:
        rating_data = await backend_client.get_rating(message.from_user.id)
        rating_value = rating_data.get("rating")
        if rating_value is None:
            rating_value = 0.0
        await message.answer(f"Твой рейтинг: {float(rating_value):.2f}")
    except Exception as e:
        logger.error("Failed to fetch rating for %d: %s", message.from_user.id, e)
        await message.answer("Не удалось загрузить рейтинг")


@router.message(F.text == "Искать пару")
async def search_partner(message: Message, state: FSMContext):
    await _send_next_candidate(message, state)


@router.callback_query(F.data.startswith("action:"), SearchStates.waiting_for_action)
async def process_search_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    candidate_id = data.get("current_candidate_id")

    if candidate_id is None:
        await callback.answer("Анкета не найдена", show_alert=True)
        await state.clear()
        return

    is_like = action == "like"
    try:
        await backend_client.send_interaction(
            requester_id=callback.from_user.id,
            responser_id=candidate_id,
            is_like=is_like,
        )
    except Exception as e:
        logger.error("Failed to send interaction from %d to %d: %s", callback.from_user.id, candidate_id, e)
        await callback.answer("Ошибка, попробуй позже", show_alert=True)
        return

    await callback.answer("Лайк отправлен" if is_like else "Анкета пропущена")
    await callback.message.edit_reply_markup(reply_markup=None)
    await _send_next_candidate(callback.message, state)


async def _send_next_candidate(message: Message, state: FSMContext):
    try:
        candidate = await backend_client.get_search_candidate(message.from_user.id)
    except Exception as e:
        logger.error("Failed to search candidate for %d: %s", message.from_user.id, e)
        await message.answer("Не удалось найти анкету. Попробуй позже.")
        return

    if not candidate:
        await state.clear()
        await message.answer("Подходящих анкет пока нет. Попробуй позже.")
        return

    await state.set_state(SearchStates.waiting_for_action)
    await state.update_data(current_candidate_id=candidate["telegram_id"])
    candidate_rating = candidate.get("rating")
    if candidate_rating is None:
        candidate_rating = 0.0

    text = (
        "Найдена анкета:\n\n"
        f"Возраст: {candidate.get('age', '—')}\n"
        f"Пол: {candidate.get('gender', '—')}\n"
        f"Интересы: {candidate.get('interests', '—')}\n"
        f"Город: {candidate.get('city', '—')}\n"
        f"Рейтинг: {float(candidate_rating):.2f}"
    )
    await message.answer(text, reply_markup=get_like_dislike_keyboard())
