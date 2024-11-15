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

# Вставьте ваш токен бота
TELEGRAM_TOKEN = "7861495333:AAGFdhHavI5gd1_DRVtilAd-O2qmcA8iDeo"  # Замените на ваш токен

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

# Словарь для отслеживания количества команд от пользователей
user_commands_count = {}

# Проверка тревоги для Киева
def check_kyiv_alert():
    """Проверяет тревогу в Киеве на сайте https://map.ukrainealarm.com/."""
    url = 'https://map.ukrainealarm.com/'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            kyiv_status = soup.find('div', class_='Kyiv')  # Убедитесь, что это правильный селектор
            if kyiv_status and 'Тривога' in kyiv_status.text:
                return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке тревоги: {e}")
        return False

# Отправка сообщения и изображения в Telegram
def send_alert_message(chat_id):
    """Отправляет сообщение и изображение о тревоге в Telegram."""
    message = "Палундра !!! Мы все обкакаемся! Тревога Киев"
    image_url = "https://raw.githubusercontent.com/morsikha/lashelov/main/alert.jpg"

    try:
        bot.send_message(chat_id=chat_id, text=message)
        bot.send_photo(chat_id=chat_id, photo=image_url)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения или изображения: {e}")

# Планировщик задач
def start_scheduler(chat_id):
    """Запускает планировщик для регулярной проверки тревог."""
    def job():
        if check_kyiv_alert():
            send_alert_message(chat_id)

    schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Функции для команд
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

def get_meme():
    return "https://raw.githubusercontent.com/morsikha/lashelov/main/alert.jpg"

def get_ukrainian_joke():
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка входящих сообщений."""
    user_id = update.effective_user.id  # ID пользователя
    chat_id = update.effective_chat.id  # ID чата или группы
    user_message = update.message.text.lower()  # Текст сообщения в нижнем регистре
    logger.info(f"DEBUG: {update}")

    # Логируем ID чата/группы и входящее сообщение
    logger.info(f"ID чата: {chat_id}, сообщение от {update.effective_user.username} ({user_id}): {user_message}")
    logger.info(f"Получено сообщение: {update.message.text}")
    logger.info(f"ID чата: {update.effective_chat.id}")

    # Если это групповая беседа, логируем тип чата
    if update.effective_chat.type in ["group", "supergroup"]:
        logger.info(f"Сообщение пришло из группы: {update.effective_chat.title} (ID: {chat_id})")

    # Инициализация счётчика для нового пользователя
    if user_id not in user_commands_count:
        user_commands_count[user_id] = 0

    # Увеличение счётчика при использовании команд
    if any(cmd in user_message for cmd in ["курс", "биток", "анекдот", "мем"]):
        user_commands_count[user_id] += 1
        logger.info(f"Пользователь {user_id} отправил {user_commands_count[user_id]} команд(ы).")

        # Проверка лимита использования команд
        if user_commands_count[user_id] >= 3:
            await context.bot.send_message(chat_id=chat_id, text="Вы очманели, я устал! Иди ловить ляща!")
            return  # Прекращаем обработку команды, если превышен лимит

    # Реакция на команды
    if "курс" in user_message:
        rates_message = get_fish_rates()
        await context.bot.send_message(chat_id=chat_id, text=rates_message)

    elif "биток" in user_message:
        btc_message = get_bitcoin_rate()
        await context.bot.send_message(chat_id=chat_id, text=btc_message)

    elif "мем" in user_message:
        meme_url = get_meme()
        await context.bot.send_photo(chat_id=chat_id, photo=meme_url)

    elif "анекдот" in user_message:
        joke_message = get_ukrainian_joke()
        await context.bot.send_message(chat_id=chat_id, text=joke_message)

    # Дополнительные реакции на ключевые слова
    if any(word in user_message for word in ["кс", "cs", "катка", "катку"]):
        await context.bot.send_message(chat_id=chat_id, text="задрот")

# Основной запуск бота
def main():
    print("Запуск бота...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    app.add_handler(text_handler)

    # Для планировщика запускаем в отдельном потоке
    chat_id = "ВАШ_CHAT_ID"  # Замените на ваш ID чата
    t = Thread(target=start_scheduler, args=(chat_id,))
    t.start()
    
 # Добавление обработчика для отладки
    debug_handler = MessageHandler(filters.ALL, debug_update)
    app.add_handler(debug_handler)
    
    keep_alive()
    app.run_polling()

if __name__ == '__main__':
    main()
