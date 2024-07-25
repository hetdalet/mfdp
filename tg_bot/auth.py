from telebot import types
from core_api import core_api


def extract_token(text: str):
    if not text:
        return
    splitted = text.split(" ")
    if len(splitted) != 2 or splitted[0] != '/start':
        return
    token = splitted[1].strip()
    return token


def send_link_account_msg(bot, user_id, token):
    markup = types.InlineKeyboardMarkup()
    yes_btn = types.InlineKeyboardButton(
        text='Yes',
        callback_data="link_acc:" + token
    )
    markup.add(yes_btn)
    bot.send_message(user_id, "Привязать аккаунт?", reply_markup=markup)


def link_account(bot, tg_user_id, token):
    response = core_api.post(
        f"/users/tg/link_acc",
        data={"link_token": token, "tg_user_id": tg_user_id}
    )
    if response.status_code == 200:
        msg = "Account successfully linked"
    else:
        msg = response.text
    bot.send_message(tg_user_id, msg)
