import os
import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# --- Keyboards ---

def main_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("HOROSCOPE"))
    kb.row(KeyboardButton("HELP"))
    kb.row(KeyboardButton("INFO"))
    return kb

def zodiac_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    signs = [
        "Aries", "Taurus", "Gemini",
        "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius",
        "Capricorn", "Aquarius", "Pisces"
    ]
    # Добавляем кнопки по 3 в ряд, чтобы выглядело аккуратно
    row = []
    for i, sign in enumerate(signs, start=1):
        row.append(KeyboardButton(sign))
        if i % 3 == 0:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    kb.row(KeyboardButton("MENU"), KeyboardButton("CANCEL"))
    return kb


def day_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(
        KeyboardButton("TODAY"),
        KeyboardButton("TOMORROW"),
        KeyboardButton("YESTERDAY"),
    )
    kb.row(KeyboardButton("MENU"), KeyboardButton("CANCEL"))
    return kb

# --- API call ---

def get_daily_horoscope(sign: str, day: str) -> dict:
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign, "day": day}
    response = requests.get(url, params=params, timeout=15)
    return response.json()

# --- Handlers ---

def go_to_menu(chat_id: int , text: str = "Choose an option:"):
    bot.send_message(chat_id, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=["start", "hello"])
def send_welcome(message):
    go_to_menu(message.chat.id, "I am Baibacci and horoscope believer. Choose an option:")



@bot.message_handler(commands=["horoscope"])
def sign_handler(message):
    bot.send_message(
        message.chat.id,
        "Choose your zodiac sign:",
        reply_markup=zodiac_keyboard()
    )
    # ждём следующий ввод (нажатие кнопки) — это будет знак
    bot.register_next_step_handler(message, day_handler)

def day_handler(message):
    sign = (message.text or "").strip()
    if sign.upper() == "CANCEL":
        go_to_menu(message.chat.id, "Cancelled. Choose an option:")
        return
    if sign.upper() == "MENU":
        go_to_menu(message.chat.id)
        return

    valid_signs = {
        "aries","taurus","gemini","cancer","leo","virgo",
        "libra","scorpio","sagittarius","capricorn","aquarius","pisces"
    }
    if sign.lower() not in valid_signs:
        bot.send_message(
            message.chat.id,
            "Please choose a zodiac sign using the buttons.",
            reply_markup=zodiac_keyboard()
        )
        bot.register_next_step_handler(message, day_handler)
        return

    bot.send_message(
        message.chat.id,
        "Choose the day:",
        reply_markup=day_keyboard()
    )
    bot.register_next_step_handler(message, fetch_horoscope, sign.lower())

def fetch_horoscope(message, sign):
    day = (message.text or "").strip().upper()
    if day in {"CANCEL", "MENU"}:
        go_to_menu(message.chat.id, "Cancelled. Choose an option:")
        return
    allowed_days = {"TODAY", "TOMORROW", "YESTERDAY"}
    # Разрешаем также дату YYYY-MM-DD
    is_date = False
    if len(day) == 10 and day[4] == "-" and day[7] == "-":
        is_date = True

    if day not in allowed_days and not is_date:
        bot.send_message(
            message.chat.id,
            "Please choose TODAY / TOMORROW / YESTERDAY or enter a date in YYYY-MM-DD format.",
            reply_markup=day_keyboard()
        )
        bot.register_next_step_handler(message, fetch_horoscope, sign)
        return

    try:
        horoscope = get_daily_horoscope(sign, day)
        data = horoscope.get("data", {})
        horoscope_text = data.get("horoscope_data", "No data returned.")
        date_text = data.get("date", day)

        horoscope_message = (
            f"*Horoscope:* {horoscope_text}\n"
            f"*Sign:* {sign.capitalize()}\n"
            f"*Day:* {date_text}"
        )

        go_to_menu(message.chat.id, "Here's your horoscope!")
        bot.send_message(message.chat.id, horoscope_message, parse_mode="Markdown")
    except Exception:
        bot.send_message(message.chat.id, "Something went wrong. Please try again later.")


@bot.message_handler(commands=["help"])
def help_handler(message):
    text = (
        "Available commands:\n"
        "/start - greeting\n"
        "/horoscope - get daily horoscope\n"
        "/help - show this help message\n"
        "/info - info about the bot\n"
        "\n"
        "Tip: use the buttons to choose sign and day"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=["info"])
def info_handler(message):
    text = (
        "This Bot is made for educational purposes only and has no relation to any real person\n"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())



@bot.message_handler(func=lambda msg: msg.text in {"MENU", "HOROSCOPE", "HELP", "INFO"})
def menu_router(message):
    if message.text == "HELP":
        help_handler(message)
        return
    if message.text == "INFO":
        info_handler(message)
        return

    # HOROSCOPE или MENU ведут к сценарию гороскопа
    bot.send_message(
        message.chat.id,
        "Choose your zodiac sign:",
        reply_markup=zodiac_keyboard()
    )
    bot.register_next_step_handler(message, day_handler)

# Optional: simple fallback for non-command text (doesn't echo commands)
@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith("/"))
def fallback(message):
    bot.send_message(message.chat.id, "Type /horoscope to get a horoscope.")

bot.infinity_polling()
