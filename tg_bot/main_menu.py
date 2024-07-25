from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton


def show(bot, user_id, replace=True):
    main_menu = InlineKeyboardMarkup(row_width=1)
    account_btn = InlineKeyboardButton(
        'Аккаунт',
        callback_data='acc'
    )
    models_btn = InlineKeyboardButton(
        'Оценить дом',
        callback_data='evaluate'
    )
    main_menu.add(account_btn)
    main_menu.add(models_btn)
    bot.send_message(user_id, "Главное меню", reply_markup=main_menu)
