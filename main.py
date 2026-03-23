import requests
import datetime
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import time
from zoneinfo import ZoneInfo
# from dotenv import load_dotenv
# load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")

LAT = 45.035470
LON = 38.975313

# Перевод состояний погоды
CONDITIONS = {
    "clear": "☀️ Ясно",
    "partly-cloudy": "🌤 Малооблачно",
    "cloudy": "☁️ Облачно",
    "overcast": "🌥 Пасмурно",
    "light-rain": "🌦 Небольшой дождь",
    "rain": "🌧 Дождь",
    "heavy-rain": "⛈ Сильный дождь",
    "snow": "❄️ Снег",
    "thunderstorm": "⛈ Гроза"
}


def get_weather(days=1):
    url = "https://api.weather.yandex.ru/v2/forecast"
    headers = {"X-Yandex-API-Key": YANDEX_API_KEY}
    params = {
        "lat": LAT,
        "lon": LON,
        "lang": "ru_RU",
        "limit": days
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    fact = data["fact"]
    forecasts = data["forecasts"]

    condition = CONDITIONS.get(fact["condition"], fact["condition"])

    text = f"""
🌆 <b>Погода в Краснодаре</b>

🌡 Сейчас: {fact['temp']}°C (ощущается {fact['feels_like']}°C)
💨 Ветер: {fact['wind_speed']} м/с
☁️ {condition}
"""

    # прогноз на несколько дней
    if days > 1:
        text += "\n📅 <b>Прогноз:</b>\n"

        for day in forecasts:
            date = day["date"]
            part = day["parts"]["day"]

            temp_min = part.get("temp_min", "?")
            temp_max = part.get("temp_max", "?")
            cond = CONDITIONS.get(part.get("condition", ""), "")

            text += f"\n📆 {date}\n🌡 {temp_min}…{temp_max}°C\n{cond}\n"

    text += "\nХорошего дня ☀️"
    return text

def get_weather_today_detailed():
    url = "https://api.weather.yandex.ru/v2/forecast"
    headers = {"X-Yandex-API-Key": YANDEX_API_KEY}
    params = {
        "lat": LAT,
        "lon": LON,
        "lang": "ru_RU",
        "limit": 1
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    fact = data["fact"]
    forecast = data["forecasts"][0]["parts"]

    condition_now = CONDITIONS.get(fact["condition"], fact["condition"])

    def part_text(name, part):
        cond = CONDITIONS.get(part.get("condition", ""), "")
        return f"{name}: {part.get('temp', '?')}°C {cond}"

    text = f"""
🌅 <b>Доброе утро!</b>

🌆 <b>Погода в Краснодаре сегодня</b>

📍 Сейчас:
🌡 {fact['temp']}°C (ощущается {fact['feels_like']}°C)
💨 Ветер: {fact['wind_speed']} м/с
☁️ {condition_now}

📅 <b>По частям дня:</b>

🌄 Утро: {forecast['morning']['temp']}°C {CONDITIONS.get(forecast['morning']['condition'], '')}
🌞 День: {forecast['day']['temp']}°C {CONDITIONS.get(forecast['day']['condition'], '')}
🌇 Вечер: {forecast['evening']['temp']}°C {CONDITIONS.get(forecast['evening']['condition'], '')}
🌙 Ночь: {forecast['night']['temp']}°C {CONDITIONS.get(forecast['night']['condition'], '')}

Хорошего дня ☀️
"""
    return text


# --- Команды ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
👋 <b>Привет! Я бот "Моя погода"</b>

📍 Погода в Краснодаре

📌 <b>Команды:</b>

/now — сейчас  
/today — сегодня  
/3days — 3 дня  
/7days — 7 дней  
/subscribe — каждое утро в 08:00 🌅
"""
    await update.message.reply_text(text, parse_mode="HTML")


async def weather_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📍 <b>Сейчас:</b>\n" + get_weather(1)
    await update.message.reply_text(text, parse_mode="HTML")


async def weather_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_weather_today_detailed()
    await update.message.reply_text(text, parse_mode="HTML")


async def weather_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_weather(3)
    await update.message.reply_text(text, parse_mode="HTML")


async def weather_7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_weather(7)
    await update.message.reply_text(text, parse_mode="HTML")


async def send_daily(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id

    text = get_weather_today_detailed()

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML"
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    context.job_queue.run_daily(
        send_daily,
        time=time(hour=8, minute=0, tzinfo=ZoneInfo("Europe/Moscow")),
        chat_id=chat_id
    )

    await update.message.reply_text("Подписка включена 🌅")


# --- Запуск ---

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("now", weather_now))
app.add_handler(CommandHandler("today", weather_today))
app.add_handler(CommandHandler("3days", weather_3))
app.add_handler(CommandHandler("7days", weather_7))
app.add_handler(CommandHandler("subscribe", subscribe))

app.run_polling()