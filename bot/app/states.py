from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_start = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_interests = State()
    waiting_for_city = State()
    waiting_for_age_preference = State()
    waiting_for_gender_preference = State()
    waiting_for_interests_preference = State()
    waiting_for_city_preference = State()


class SearchStates(StatesGroup):
    waiting_for_action = State()
