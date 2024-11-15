# -*- coding: utf-8 -*-

import random
import requests
import logging
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import schedule
import time

# Вставьте ваш токен бота и ID чата
TELEGRAM_TOKEN = "7861495333:AAGFdhHavI5gd1_DRVtilAd-O2qmcA8iDeo"  # Замените на ваш токен
CHAT_ID = "ВАШ_CHAT_ID"  # Укажите ID чата, куда бот будет отправлять уведомления

# Логгирование ошибок
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка Telegram Bot API
bot = Bot(token=TELEGRAM_TOKEN)

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

# Проверка тревоги для Киева
def check_kyiv_alert():
    """Проверяет тревогу в Киеве на сайте https://map.ukrainealarm.com/."""
    url = 'https://map.ukrainealarm.com/'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            kyiv_status = soup.find('div', class_='Kyiv')  # Обновите класс или ID, если он изменится
            if kyiv_status and 'Тривога' in kyiv_status.text:
                return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке тревоги: {e}")
        return False

# Отправка сообщения в Telegram
def send_alert_message():
    """Отправляет сообщение о тревоге в Telegram."""
    message = "Палундра !!! Мы все обкакаемся! Тревога Киев"
    bot.send_message(chat_id=CHAT_ID, text=message)

# Регулярная проверка тревог
def job():
    if check_kyiv_alert():
        send_alert_message()

# Планировщик задач
def start_scheduler():
    """Запускает планировщик для регулярной проверки тревог."""
    schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Другие функции (например, для обработки сообщений в чате)
fish_list = ["карась", "лещ", "плотва", "тунец", "акула"]

def get_fish_rates():
    rates = {fish: round(random.uniform(10, 1000), 2) for fish in fish_list}
    rate_message = "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])
    return f"🐟 Текущие курсы рыбешки:\n\n{rate_message}"

def get_bitcoin_rate():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        btc_price = data["bitcoin"]["usd"]
        return f"💰 Курс биткоина: ${btc_price} USD"
    else:
        return "Не удалось получить курс биткоина."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка входящих сообщений."""
    user_message = update.message.text.lower()

    if any(word in user_message for word in ["кс", "cs", "катка", "катку"]):
        await update.message.reply_text("задрот")
    elif "курс" in user_message:
        rates_message = get_fish_rates()
        await update.message.reply_text(rates_message)
    elif "биток" in user_message:
        btc_message = get_bitcoin_rate()
        await update.message.reply_text(btc_message)

# Основной запуск бота
def main():
    print("Запуск бота...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    app.add_handler(text_handler)

    t = Thread(target=start_scheduler)
    t.start()

    app.run_polling()

if __name__ == '__main__':
    keep_alive()  # Запуск веб-сервера
    main()        # Запуск бота
