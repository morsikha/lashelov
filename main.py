# -*- coding: utf-8 -*-
import random
import requests
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import schedule
import time

# Вставьте ваш токен бота
TELEGRAM_TOKEN = "Ваш_токен_здесь"  # Укажите реальный токен

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot
app = Application.builder().token(TELEGRAM_TOKEN).build()

# Flask-сервер для поддержания активности
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

# Проверка тревоги в Киеве
def check_kyiv_alert():
    url = 'https://map.ukrainealarm.com/'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            kyiv_status = soup.find('div', class_='Kyiv')  # Проверьте селектор
            if kyiv_status and 'Тривога' in kyiv_status.text:
                return True
    except Exception as e:
        logger.error(f"Ошибка при проверке тревоги: {e}")
    return False

async def send_alert_message(chat_id: int):
    message = "Палундра !!! Мы все обкакаемся! Тревога Киев"
    image_url = "https://raw.githubusercontent.com/morsikha/lashelov/main/alert.jpg"
    try:
        await app.bot.send_message(chat_id=chat_id, text=message)
        await app.bot.send_photo(chat_id=chat_id, photo=image_url)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")

def start_scheduler(chat_id: int):
    def job():
        if check_kyiv_alert():
            app.create_task(send_alert_message(chat_id))  # Асинхронный вызов

    schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Основной обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    chat_id = update.effective_chat.id

    if "курс" in user_message:
        rates = {fish: round(random.uniform(10, 1000), 2) for fish in ["карась", "лещ", "плотва", "тунец", "акула"]}
        rates_message = "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])
        await context.bot.send_message(chat_id=chat_id, text=f"🐟 Текущие курсы рыбешки:\n\n{rates_message}")

    elif "биток" in user_message:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url)
        if response.status_code == 200:
            btc_price = response.json()["bitcoin"]["usd"]
            await context.bot.send_message(chat_id=chat_id, text=f"💰 Курс биткоина: ${btc_price} USD")
        else:
            await context.bot.send_message(chat_id=chat_id, text="Не удалось получить курс биткоина.")

    elif "анекдот" in user_message:
        url = "https://rozdil.lviv.ua/anekdot/"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            jokes = [joke.get_text().strip() for joke in soup.find_all("a", class_="hoveranek black")]
            joke = random.choice(jokes) if jokes else "Анекдоты не найдены."
            await context.bot.send_message(chat_id=chat_id, text=joke)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Ошибка получения анекдотов.")

    elif "мем" in user_message:
        meme_url = "https://raw.githubusercontent.com/morsikha/lashelov/main/alert.jpg"
        await context.bot.send_photo(chat_id=chat_id, photo=meme_url)

async def debug_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Отладочное сообщение: {update}")

# Основной запуск
def main():
    print("Запуск бота...")

    # Обработчики
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.ALL, debug_update))

    # Планировщик в отдельном потоке
    chat_id = 123456789  # Замените на ваш реальный chat_id
    Thread(target=start_scheduler, args=(chat_id,)).start()

    keep_alive()  # Поддержание активности
    app.run_polling()

if __name__ == '__main__':
    main()
