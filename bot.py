import os
import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# --- Keyboards ---

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
    return kb

def day_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(
        KeyboardButton("TODAY"),
        KeyboardButton("TOMORROW"),
        KeyboardButton("YESTERDAY"),
    )
    kb.row(KeyboardButton("CANCEL"))
    return kb

# --- API call ---

def get_daily_horoscope(sign: str, day: str) -> dict:
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign, "day": day}
    response = requests.get(url, params=params, timeout=15)
    return response.json()

# --- Handlers ---

@bot.message_handler(commands=["start", "hello"])
def send_welcome(message):
    bot.reply_to(message, "I am Baibacci and horoscope believer. Type /horoscope to begin.")

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
        bot.send_message(message.chat.id, "Cancelled. Type /horoscope to start again.")
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
    if day == "CANCEL":
        bot.send_message(message.chat.id, "Cancelled. Type /horoscope to start again.")
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

        bot.send_message(message.chat.id, "Here's your horoscope!", reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id, horoscope_message, parse_mode="Markdown")
    except Exception:
        bot.send_message(message.chat.id, "Something went wrong. Please try again later.")

# Optional: simple fallback for non-command text (doesn't echo commands)
@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith("/"))
def fallback(message):
    bot.send_message(message.chat.id, "Type /horoscope to get a horoscope.")

bot.infinity_polling()
