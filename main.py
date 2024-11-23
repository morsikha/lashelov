# -*- coding: utf-8 -*-
import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import schedule
import time

# Вставьте ваш токен бота
TELEGRAM_TOKEN = "7861495333:AAGb8W-B4nFg0cM8cnmLJRCbLcTpG5yQxWI"

# Вставьте ваш API-ключ OpenWeatherMap
OPENWEATHER_API_KEY = "f90904c2ab88b6543e799322389c4c31"

# URL для картинки при тревоге
ALERT_IMAGE_URL = "https://raw.githubusercontent.com/ваш-репозиторий/alert.jpg"

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask-сервер для поддержания активности
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает!"

@flask_app.route('/health')
def health_check():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_flask).start()

# Планировщик
def scheduler(app):
    schedule.every(1).minutes.do(lambda: app.create_task(send_alert_to_groups(app)))

# Функция для отправки тревоги в Telegram-группы
async def send_alert_to_groups(app: Application):
    try:
        message = "🚨 Увага! летит якась какашка!"
        async with app.bot:
            updates = await app.bot.get_updates()
            for update in updates:
                if update.message and update.message.chat.type in ["group", "supergroup"]:
                    chat_id = update.message.chat.id
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=message)
                        await app.bot.send_photo(chat_id=chat_id, photo=ALERT_IMAGE_URL)
                    except TelegramError as e:
                        logger.error(f"Ошибка отправки в группу {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений: {e}")

# Функция для получения криптовалют
def get_bitcoin_and_other_currencies():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,ripple,cardano,solana&vs_currencies=usd"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return "\n".join([f"{coin.capitalize()}: ${price['usd']}" for coin, price in data.items()])
        return "Ошибка при получении курсов криптовалют."
    except Exception as e:
        logger.error(f"Ошибка получения курсов криптовалют: {e}")
        return "Произошла ошибка при загрузке курсов."

# Функция для получения анекдотов
def get_joke():
    url = "https://rozdil.lviv.ua/anekdot/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            jokes = [joke.get_text().strip() for joke in soup.find_all("div", class_="anekdot")]
            return random.choice(jokes) if jokes else "Анекдоты временно недоступны."
        return "Ошибка загрузки анекдотов."
    except Exception as e:
        logger.error(f"Ошибка загрузки анекдотов: {e}")
        return "Произошла ошибка при загрузке анекдотов."

# Функция для погоды
def get_weather():
    city = "Kyiv"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            temp = round(data['main']['temp'])
            description = data['weather'][0]['description']
            return f"Погода в {city}: {temp}°C, {description.capitalize()}"
        return "Не удалось получить данные о погоде."
    except Exception as e:
        logger.error(f"Ошибка получения погоды: {e}")
        return "Произошла ошибка при загрузке данных о погоде."

# Функция для случайных мемов
def get_random_meme():
    url = "https://api.imgflip.com/get_memes"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            memes = response.json().get("data", {}).get("memes", [])
            return random.choice(memes)["url"] if memes else "Не удалось найти мемы."
        return "Ошибка при загрузке мемов."
    except Exception as e:
        logger.error(f"Ошибка загрузки мемов: {e}")
        return "Произошла ошибка при загрузке мемов."

# Функция для матчей
def get_upcoming_matches():
    url = "https://hltv-api.vercel.app/api/matches"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            matches = response.json()
            if matches:
                upcoming = [f"{match.get('time')}: {' vs '.join([t.get('name', 'Unknown') for t in match.get('teams', [])])}" for match in matches[:8]]
                return "\n".join(upcoming) if upcoming else "Нет ближайших матчей."
        return "Ошибка загрузки матчей."
    except Exception as e:
        logger.error(f"Ошибка загрузки матчей: {e}")
        return "Произошла ошибка при загрузке матчей."

# Основной обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    chat_id = update.effective_chat.id

    if "погода" in user_message:
        await context.bot.send_message(chat_id=chat_id, text=get_weather())

    elif "кс" in user_message or "катка" in user_message:
        phrases = ["Настоящий задрот КС!", "Эй, чемпион, твоя катка ждёт!"]
        await context.bot.send_message(chat_id=chat_id, text=random.choice(phrases))

    elif "гейм" in user_message:
        await context.bot.send_message(chat_id=chat_id, text=get_upcoming_matches())

    elif "курс" in user_message:
        rates = {fish: round(random.uniform(10, 1000), 2) for fish in ["карась", "лещ", "плотва", "тунец", "акула"]}
        rates_message = "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])
        await context.bot.send_message(chat_id=chat_id, text=f"🐟 Курсы рыб:\n\n{rates_message}")

    elif "биток" in user_message:
        await context.bot.send_message(chat_id=chat_id, text=get_bitcoin_and_other_currencies())

    elif "анекдот" in user_message:
        await context.bot.send_message(chat_id=chat_id, text=get_joke())

    elif "мем" in user_message:
        meme_url = get_random_meme()
        if meme_url.startswith("http"):
            await context.bot.send_photo(chat_id=chat_id, photo=meme_url)
        else:
            await context.bot.send_message(chat_id=chat_id, text=meme_url)

# Запуск бота
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    scheduler(app)
    keep_alive()
    Thread(target=schedule.run_pending).start()
    app.run_polling()

if __name__ == "__main__":
    main()
