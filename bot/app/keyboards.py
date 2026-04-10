from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Начать регистрацию")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужской", callback_data="gender:male"),
                InlineKeyboardButton(text="Женский", callback_data="gender:female"),
            ],
            [InlineKeyboardButton(text="Другой", callback_data="gender:other")],
        ]
    )


def get_gender_preference_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужчин", callback_data="gender_pref:male"),
                InlineKeyboardButton(text="Женщин", callback_data="gender_pref:female"),
            ],
            [InlineKeyboardButton(text="Всех", callback_data="gender_pref:all")],
        ]
    )


def get_like_dislike_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Нравится", callback_data="action:like"),
                InlineKeyboardButton(text="Пропустить", callback_data="action:skip"),
            ],
        ]
    )


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Искать пару")],
            [KeyboardButton(text="Мой профиль"), KeyboardButton(text="Мой рейтинг")],
        ],
        resize_keyboard=True,
    )
