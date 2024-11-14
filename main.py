# -*- coding: utf-8 -*-

import random
import requests
import logging
import feedparser
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# Вставьте ваш токен бота напрямую здесь
TELEGRAM_TOKEN = "7861495333:AAGFdhHavI5gd1_DRVtilAd-O2qmcA8iDeo"  # Замените на ваш токен

# Логгирование ошибок
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка веб-сервера для поддержания активности
app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Список с рыбой и её случайными "курсами"
fish_list = ["карась", "лещ", "плотва", "тунец", "акула"]

def get_fish_rates():
    """Функция для генерации случайных "курсов" рыбы к гривне."""
    rates = {fish: round(random.uniform(10, 1000), 2) for fish in fish_list}
    rate_message = "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])
    return f"🐟 Текущие курсы рыбешки:\n\n{rate_message}"

def get_bitcoin_rate():
    """Функция для получения курса биткоина в долларах."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        btc_price = data["bitcoin"]["usd"]
        return f"💰 Курс биткоина: ${btc_price} USD"
    else:
        return "Не удалось получить курс биткоина."

def get_ukrainian_joke():
    """Функция для получения случайного анекдота с сайта."""
    url = "https://rozdil.lviv.ua/anekdot/"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        jokes = [joke.get_text().strip() for joke in soup.find_all("a", class_="hoveranek black")]

        if jokes:
            return random.choice(jokes)
        else:
            return "Не удалось найти анекдоты на странице."
    else:
        return "Не удалось получить анекдоты. Попробуйте позже."

def get_random_meme():
    """Функция для получения случайного мема из API Imgflip."""
    url = "https://api.imgflip.com/get_memes"
    response = requests.get(url)
    data = response.json()
    if data["success"]:
        memes = data["data"]["memes"]
        meme = random.choice(memes)
        return meme["url"]
    else:
        return "Не удалось получить мем."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция, вызываемая при любом текстовом сообщении."""
    user_message = update.message.text.lower()

    if "курс" in user_message:
        rates_message = get_fish_rates()
        await update.message.reply_text(rates_message)
    elif "биток" in user_message:
        btc_message = get_bitcoin_rate()
        await update.message.reply_text(btc_message)
    elif "анекдот" in user_message:  # Команда "анекдот"
        joke_message = get_ukrainian_joke()
        await update.message.reply_text(joke_message)
    elif "мем" in user_message:  # Команда "мем"
        meme_url = get_random_meme()
        if meme_url != "Не удалось получить мем.":
            await update.message.reply_photo(meme_url)
        else:
            await update.message.reply_text(meme_url)

async def error_handler(update, context):
    """Обработчик ошибок."""
    logger.error(f"Произошла ошибка: {context.error}")

def main():
    print("Запуск бота...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    app.add_handler(text_handler)

    # Обработчик ошибок
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == '__main__':
    keep_alive()  # Запуск веб-сервера для поддержания активности
    main()        # Запуск бота
