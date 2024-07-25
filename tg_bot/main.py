import functools
import os
import evaluation

import telebot
from telebot import types

from account import deposit
from account import show_balance
from auth import extract_token
from auth import link_account
from auth import send_link_account_msg
from core_api import core_api
from core_api import get_session
from core_api import poll_task
from main_menu import show as show_main_menu


std_log = functools.partial(print, flush=True)
with open(os.getenv("TG_API_TOKEN_FILE")) as token_file:
    TOKEN = token_file.read().strip()
    std_log('TOKEN')

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    session = get_session(user_id)
    print('BOT START', 1)
    if session:
        show_main_menu(bot, user_id, replace=False)
        return

    print('BOT START', 2)
    link_token = extract_token(message.text)
    if link_token:
        send_link_account_msg(bot, message.from_user.id, link_token)
        return

    print('BOT START', 3)
    response = core_api.get(f"/users/tg/{user_id}")
    if response.status_code == 404:
        bot.send_message(
            user_id,
            "Link Telegram account to cloud account"
        )


@bot.callback_query_handler(func=lambda c: c.data == "main")
def show_main_menu_hdl(callback_query: types.CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    show_main_menu(bot, callback_query.from_user.id)


@bot.callback_query_handler(func=lambda c: c.data == "acc")
def show_balance_hdl(callback_query: types.CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    show_balance(bot, callback_query.from_user.id, callback_query.message)


@bot.callback_query_handler(func=lambda c: c.data.startswith("dep"))
def deposit_hdl(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    _, amount = callback_query.data.split(":")
    code, result = deposit(user_id, float(amount))
    text = None
    if code != 200:
        text = f"Error: {result}"
    bot.answer_callback_query(callback_query.id)
    show_balance(bot, user_id, callback_query.message, text)


@bot.callback_query_handler(func=lambda c: c.data.startswith("link_acc:"))
def link_account_hdl(callback_query: types.CallbackQuery):
    print('LINK_TELEGRAM_ACCOUNT', flush=True)
    bot.answer_callback_query(callback_query.id)
    token = callback_query.data.removeprefix("link_acc:")
    link_account(bot, callback_query.from_user.id, token)


@bot.callback_query_handler(func=lambda c: c.data.startswith("evaluate"))
def request_location_hdl(callback_query: types.CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    evaluation.request_location(
        bot,
        callback_query.from_user.id
    )


@bot.callback_query_handler(func=lambda c: c.data == "coords")
def request_coords_hdl(callback_query: types.CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    evaluation.request_coords(bot, callback_query.from_user.id)


@bot.callback_query_handler(func=lambda c: c.data == "address")
def read_address_hdl(callback_query: types.CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    message = callback_query.message
    lat, lon = evaluation.fetch_coords(message.text)
    if not lat or not lon:
        bot.send_message(
            user_id,
            "Не удалось определить расположение дома."
        )
        return
    bot.send_message(user_id, "Ввод прочих параметров")


@bot.callback_query_handler(func=lambda c: c.data.startswith("construction"))
def read_construction_hdl(callback_query: types.CallbackQuery):
    handle_callback_query(
        callback_query,
        evaluation.request_year,
        value_type=int
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("land_type"))
def read_land_type_hdl(callback_query: types.CallbackQuery):
    handle_callback_query(
        callback_query,
        evaluation.request_heating_type,
        value_type=int
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("heating_type"))
def request_heating_type_hdl(callback_query: types.CallbackQuery):
    handle_callback_query(
        callback_query,
        evaluation.request_sewerage_type,
        value_type=int
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("sewerage_type"))
def request_sewerage_type_hdl(callback_query: types.CallbackQuery):
    handle_callback_query(
        callback_query,
        evaluation.request_garage,
        value_type=int
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("garage"))
def request_garage_hdl(callback_query: types.CallbackQuery):
    handle_callback_query(
        callback_query,
        evaluation.request_bathhouse,
        value_type=int
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("bathhouse"))
def request_bathhouse_hdl(callback_query: types.CallbackQuery):
    handle_callback_query(
        callback_query,
        evaluation.request_swimming_pool,
        value_type=int
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("swimming_pool"))
def request_swimming_pool_hdl(callback_query: types.CallbackQuery):
    handle_callback_query(
        callback_query,
        evaluation.request_security,
        value_type=int
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("security"))
def request_security_hdl(callback_query: types.CallbackQuery):
    handle_callback_query(callback_query, value_type=int)
    user_id = callback_query.from_user.id
    evaluation.show_waiting_message(bot, user_id)
    evaluation.call_model(bot, user_id)


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    tg_user_id = message.from_user.id
    session = get_session(tg_user_id)
    state = session.state
    if state == 'read_coords':
        evaluation.read_coords(bot, tg_user_id, message.text)
        evaluation.request_area(bot, tg_user_id)
    elif state == "read_area":
        evaluation.read_area(bot, tg_user_id, message.text)
        evaluation.request_construction(bot, tg_user_id)
    elif state == "read_year":
        evaluation.read_year(bot, tg_user_id, message.text)
        evaluation.request_land_area(bot, tg_user_id)
    elif state == "read_land_area":
        evaluation.read_land_area(bot, tg_user_id, message.text)
        evaluation.request_land_type(bot, tg_user_id)


def handle_callback_query(callback_query: types.CallbackQuery,
                          next_handler=None,
                          value_type=None):
    std_log(callback_query.data)
    bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    evaluation.read_option(user_id, callback_query.data, value_type)
    if next_handler:
        next_handler(bot, user_id)


if __name__ == '__main__':
    print('POLLING', flush=True)
    bot.polling()
