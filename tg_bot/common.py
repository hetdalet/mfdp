from telebot.types import InlineKeyboardButton
from core_api import get_session
from core_api import update_session

GO_BACK = "Назад"
GO_TO_MAIN_BTN = InlineKeyboardButton(
    "« В главное меню",
    callback_data='main'
)


def set_state(user_id: int, state: str):
    update_session(user_id, {"state": state})


def update_input(user_id, update: dict):
    session = get_session(user_id)
    user_input = session.input or {}
    user_input.update(update)
    update_session(user_id, {"input": user_input})
