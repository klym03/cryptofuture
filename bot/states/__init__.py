from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_for_user_search = State()
    waiting_for_grant_subscription_user = State()
    waiting_for_grant_tries_user = State()
    waiting_for_referral_name = State()
    waiting_for_referral_owner = State()
    waiting_for_referral_link_name = State()
