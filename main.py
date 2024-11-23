# -*- coding: utf-8 -*-
import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# Telegram Bot Token
TELEGRAM_TOKEN = "7861495333:AAGb8W-B4nFg0cM8cnmLJRCbLcTpG5yQxWI"

# OpenWeatherMap API Key
OPENWEATHER_API_KEY = "f90904c2ab88b6543e799322389c4c31"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App for Keep-Alive
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_flask).start()

# Функция получения матчей CS2 через HLTV API
def get_upcoming_matches():
    url = "https://hltv-api.vercel.app/api/matches"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            matches = response.json()
            upcoming_matches = []
            for match in matches[:10]:  # Показываем первые 10 матчей
                teams = ", ".join([team.get("name", "Unknown") for team in match.get("teams", [])])
                time = match.get("time", "Неизвестно")
                upcoming_matches.append(f"{time}: {teams}")
            return "\n".join(upcoming_matches) if upcoming_matches else "Нет ближайших матчей."
        logger.error(f"Ошибка HTTP {response.status_code} при получении матчей.")
        return "Ошибка при получении списка матчей. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при загрузке матчей: {e}")
        return "Произошла ошибка при загрузке матчей. Попробуйте позже."

# Функция получения курса криптовалют
def get_bitcoin_and_other_currencies():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,ripple,cardano,solana&vs_currencies=usd"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return "\n".join([f"{coin.capitalize()}: ${price['usd']}" for coin, price in data.items()])
        logger.error(f"Ошибка HTTP {response.status_code} при получении курсов криптовалют.")
        return "Ошибка при получении курсов криптовалют. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при загрузке криптовалют: {e}")
        return "Произошла ошибка при загрузке курсов. Попробуйте позже."

# Функция получения случайного курса рыбы
def get_fish_rates():
    rates = {fish: round(random.uniform(10, 1000), 2) for fish in ["карась", "лещ", "плотва", "тунец", "акула"]}
    return "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])

# Функция получения случайного анекдота
def get_joke():
    url = "https://rozdil.lviv.ua/anekdot/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            jokes = [joke.get_text().strip() for joke in soup.find_all("a", class_="hoveranek black")]
            if jokes:
                return random.choice(jokes)
            logger.error("Не удалось найти анекдоты на странице.")
            return "Анекдоты временно недоступны."
        logger.error(f"Ошибка HTTP {response.status_code} при загрузке анекдотов.")
        return "Ошибка при загрузке анекдотов. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при загрузке анекдотов: {e}")
        return "Произошла ошибка при загрузке анекдотов. Попробуйте позже."

# Функция получения погоды в Киеве
def get_weather():
    city = "Kyiv"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            temp = round(data["main"]["temp"])
            description = data["weather"][0]["description"].capitalize()
            return f"Погода в {city}: {temp}°C, {description}"
        logger.error(f"Ошибка HTTP {response.status_code} при загрузке погоды.")
        return "Ошибка при загрузке данных о погоде. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при получении погоды: {e}")
        return "Произошла ошибка при загрузке данных о погоде."

# Функция получения случайного мема через API Imgflip
def get_random_meme():
    url = "https://api.imgflip.com/get_memes"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            memes = response.json().get("data", {}).get("memes", [])
            return random.choice(memes)["url"] if memes else None
        logger.error(f"Ошибка HTTP {response.status_code} при загрузке мема.")
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке мема: {e}")
        return None

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    chat_id = update.effective_chat.id

    if "гейм" in user_message:
        matches = get_upcoming_matches()
        await context.bot.send_message(chat_id, text=f"🎮 Предстоящие матчи CS2:\n\n{matches}")
    elif "биток" in user_message:
        currencies = get_bitcoin_and_other_currencies()
        await context.bot.send_message(chat_id, text=f"💰 Курс криптовалют:\n\n{currencies}")
    elif "курс" in user_message:
        fish_rates = get_fish_rates()
        await context.bot.send_message(chat_id, text=f"🐟 Курсы рыбы:\n\n{fish_rates}")
    elif "анекдот" in user_message:
        joke = get_joke()
        await context.bot.send_message(chat_id, text=joke)
    elif "мем" in user_message:
        meme_url = get_random_meme()
        if meme_url:
            await context.bot.send_photo(chat_id, photo=meme_url)
        else:
            await context.bot.send_message(chat_id, text="Не удалось загрузить мем.")
    elif "погода" in user_message:
        weather = get_weather()
        await context.bot.send_message(chat_id, text=weather)
    elif "кс" in user_message or "катка" in user_message:
        responses = [
            "Снова задрот в деле! 🎮",
            "Готовься к битве! 🔥",
            "Катка зовёт, но ты точно потянешь? 😂",
        ]
        await context.bot.send_message(chat_id, text=random.choice(responses))

# Запуск бота
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    keep_alive()
    app.run_polling()

if __name__ == "__main__":
    main()
