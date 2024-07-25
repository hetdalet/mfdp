import re

from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton
from common import update_input
from common import set_state
from common import get_session
from core_api import core_api
from core_api import poll_task


EXTRACT_FLOAT_RE = re.compile(r"[.,]?[0-9]+[.,]?[0-9]*")
EXTRACT_INT_RE = re.compile(r"[0-9]+")


def request_location(bot, user_id):
    set_state(user_id, "read_location")
    text = (
        "Сначала определим расположение дома. "
        "Это можно сделать двумя способами:"
    )
    menu = InlineKeyboardMarkup(row_width=1)
    coords_btn = InlineKeyboardButton(
        'Ввести координаты',
        callback_data='coords'
    )
    address_btn = InlineKeyboardButton(
        'Ввести адрес',
        callback_data='address'
    )
    menu.add(coords_btn)
    menu.add(address_btn)
    bot.send_message(user_id, text, reply_markup=menu)


def request_coords(bot, user_id):
    set_state(user_id, "read_coords")
    bot.send_message(
        user_id,
        "Введите координаты.\n\n"
        "Пример: 55.734096, 38.090517"
    )


def read_coords(bot, user_id, text):
    lat, lon = text.strip().split(',')
    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        lat = None
        lon = None
    if not lat or not lon:
        text = (
            "Не удалось прочитать координаты. Проверьте формат ввода "
            "и попробуйте снова."
        )
    else:
        text = f"{lat}, {lon}"
        update_input(user_id, {"lat": lat, "lon": lon})


def fetch_coords(address):
    import time
    from geopy.geocoders import Nominatim
    time.sleep(3)
    geolocator = Nominatim(user_agent='mfdp_real_estate_calculator')
    location = geolocator.geocode(address.srip())
    lat = None
    lon = None
    if location:
        lat = location.latitude
        lon = location.longitude
    return lat, lon


def request_area(bot, user_id):
    request_value(
        bot,
        user_id,
        human_name="общую площадь дома",
        unit="кв. м",
        example_input="225",
        state="read_area",
    )


def read_area(bot, user_id, text):
    read_value(
        bot,
        user_id,
        text,
        value_extractor=extract_float,
        name="area",
        human_name="общую площадь дома",
    )


def request_construction(bot, user_id):
    request_option(
        bot,
        user_id,
        state="read_construction",
        text="Выберете тип конструкции дома",
        name="construction",
        options={
            1: "кирпичный",
            2: "монолитный",
            3: "деревянный",
            4: "щитовой",
            5: "каркасный",
            6: "газобетонный блок",
            7: "пенобетонный блок",
            8: "газосиликатный блок",
        }
    )


def request_year(bot, user_id):
    request_value(
        bot,
        user_id,
        human_name="общую площадь дома",
        example_input="2007",
        state="read_year",
    )


def read_year(bot, user_id, text):
    read_value(
        bot,
        user_id,
        text,
        value_extractor=extract_int,
        name="year",
        human_name="год постройки",
    )


def request_land_area(bot, user_id):
    request_value(
        bot,
        user_id,
        human_name="общую площадь участка",
        example_input="800",
        state="read_land_area",
    )


def read_land_area(bot, user_id, text):
    read_value(
        bot,
        user_id,
        text,
        value_extractor=extract_int,
        name="land_area",
        human_name="общую площадь участка",
    )


def request_land_type(bot, user_id):
    request_option(
        bot,
        user_id,
        state="read_land_type",
        text="Выберете тип земельного участка",
        name="land_type",
        options={
            1: "ижс",
            2: "сад",
            3: "днк",
            4: "лпх",
        }
    )


def request_heating_type(bot, user_id):
    request_option(
        bot,
        user_id,
        state="read_heating_type",
        text="Выберите тип отопления",
        name="heating_type",
        options={
            1: "центральное газовое",
            2: "автономное газовое",
            3: "электрическое",
            4: "твердотопливный котел",
            5: "дизельное",
            6: "печь",
            7: "камин",
            8: "нет",
        }
    )


def request_sewerage_type(bot, user_id):
    request_option(
        bot,
        user_id,
        state="read_sewerage_type",
        text="Выберите тип канализации",
        name="sewerage_type",
        options={
            1: "центральная",
            2: "септик",
            3: "выгребная яма",
        }
    )


def request_garage(bot, user_id):
    request_option(
        bot,
        user_id,
        state="read_garage",
        text="Есть ли гараж?",
        name="garage",
        options={
            0: "нет",
            1: "да",
        }
    )


def request_bathhouse(bot, user_id):
    request_option(
        bot,
        user_id,
        state="read_bathhouse",
        text="Есть ли баня?",
        name="bathhouse",
        options={
            0: "нет",
            1: "да",
        }
    )


def request_swimming_pool(bot, user_id):
    request_option(
        bot,
        user_id,
        state="read_swimming_pool",
        text="Есть ли бассейн?",
        name="swimming_pool",
        options={
            0: "нет",
            1: "да",
        }
    )


def request_security(bot, user_id):
    request_option(
        bot,
        user_id,
        state="read_security",
        text="Есть ли охрана?",
        name="security",
        options={
            0: "нет",
            1: "да",
        }
    )


def request_value(bot,
                  user_id,
                  human_name,
                  example_input,
                  state,
                  unit=None,
                  text=None):
    set_state(user_id, state)
    if not text:
        if unit:
            text = (
                f"Введите {human_name} в {unit}. "
                "Единицы измерения указывать не нужно.\n\n "
                f"Пример: {example_input}"
            )
        else:
            text = (
                f"Введите {human_name}.\n\n"
                f"Пример: {example_input}"
            )
    bot.send_message(user_id,  text)


def read_value(bot,
               user_id,
               text,
               value_extractor,
               name,
               human_name,
               err_msg=None):
    value = value_extractor(text)
    if not value:
        if not err_msg:
            err_msg = (
                f"Не удалось прочитать {human_name}. Проверьте формат ввода "
                "и попробуйте снова."
            )
        bot.send_message(user_id, err_msg)
    else:
        update_input(user_id, {name: value})


def request_option(bot,
                   user_id,
                   state,
                   text,
                   name,
                   options):
    set_state(user_id, state)
    menu = InlineKeyboardMarkup(row_width=1)
    for option_id, option_name in options.items():
        btn = InlineKeyboardButton(
            option_name,
            callback_data=f"{name}:{option_id}"
        )
        menu.add(btn)
    bot.send_message(user_id, text, reply_markup=menu)


def read_option(user_id, option, value_type):
    name, value = option.split(":")
    if value_type:
        value = value_type(value)
    update_input(user_id, {name: value})


def extract_float(s: str):
    mo = EXTRACT_FLOAT_RE.search(s)
    if not mo:
        return
    try:
        val = float(mo.group(0))
    except ValueError:
        val = None
    return val


def extract_int(s: str):
    mo = EXTRACT_INT_RE.search(s)
    if not mo:
        return
    try:
        val = int(mo.group(0))
    except ValueError:
        val = None
    return val


def show_waiting_message(bot, user_id: int):
    bot.send_message(user_id, "Оцениваем. Подождите немного")


def call_model(bot, user_id: int):
    import json
    session = get_session(user_id)
    user_input = json.dumps(session.input)
    response = core_api.post(
        f"/services/real_estate/task",
        data={"input": user_input},
        cookies=session.cookie
    )
    if response.status_code != 200:
        bot.send_message(user_id, response.text)
        return
    task = response.json()
    response = poll_task(task["key"], cookies=session.cookie)
    if response.status_code != 200:
        bot.send_message(user_id, response.text)
        return
    task = response.json()
    output = task["output"]
    if output:
        output = f"{float(output):_.2f}".replace("_", " ")
    else:
        output = 'При обработке запроса произошла ошибка.'

    bot.send_message(user_id, output)
