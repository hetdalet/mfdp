from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton

from core_api import core_api
from core_api import get_session
from core_api import get_account_balance


def show_balance(bot, user_id, message, text=None):
    markup = InlineKeyboardMarkup(row_width=1)
    dep_10_btn = InlineKeyboardButton(
        "+10 кредитов",
        callback_data='dep:10'
    )
    dep_100_btn = InlineKeyboardButton(
        "+100 кредитов",
        callback_data='dep:100'
    )
    markup.add(dep_10_btn)
    markup.add(dep_100_btn)
    markup.add(GO_TO_MAIN_BTN)

    if not text:
        code, result = get_account_balance(user_id)
        if code == 200:
            text = f"Баланс: {result}"
        else:
            text = f"Ошибка: {result}"

    bot.edit_message_text(
        text,
        message.chat.id,
        message.message_id,
    )
    bot.edit_message_reply_markup(
        message.chat.id,
        message.message_id,
        reply_markup=markup
    )


def deposit(user_id, amount):
    session = get_session(user_id)
    response = core_api.post(
        f"/transactions/",
        data={"type": 1, "amount": amount},
        cookies=session.cookie
    )
    result = None
    if response.status_code != 200:
        result = response.json()["detail"]

    return response.status_code, result
