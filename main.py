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
ALERT_IMAGE_URL = "https://raw.githubusercontent.com/ваш-репозиторий/alert.jpg"  # Замените на реальную ссылку

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

# Функция для планировщика
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
                        logger.info(f"Уведомление отправлено в группу с chat_id: {chat_id}")
                    except TelegramError as e:
                        logger.error(f"Ошибка при отправке уведомления в группу {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений: {e}")

# Функция получения курса биткоина и других валют
def get_bitcoin_and_other_currencies():
    try:
        btc_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        btc_response = requests.get(btc_url).json()
        btc_price = btc_response.get("bitcoin", {}).get("usd", "Неизвестно")

        currencies_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,ripple,cardano,solana,polkadot&vs_currencies=usd"
        currencies_response = requests.get(currencies_url).json()

        currencies_message = ""
        for currency, details in currencies_response.items():
            currencies_message += f"{currency.capitalize()}: ${details['usd']}\n"

        return f"💰 Курс биткоина: ${btc_price} USD\n\n🌍 Другие курсы:\n{currencies_message}"
    except Exception as e:
        logger.error(f"Ошибка при получении курса валют: {e}")
        return "Ошибка при загрузке курсов. Попробуйте позже."

# Функция получения предстоящих матчей CS2
def get_upcoming_matches():
    url = "https://hltv-api.vercel.app/api/matches"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            matches = response.json()
            upcoming_matches = []
            for match in matches:
                match_time = match.get("time")
                teams = match.get("teams")
                if match_time and teams:
                    team_names = " vs ".join([team.get("name", "Unknown") for team in teams])
                    upcoming_matches.append(f"{match_time}: {team_names}")
            if upcoming_matches:
                return "\n".join(upcoming_matches[:10])  # Показываем первые 10 матчей
            else:
                return "Нет ближайших матчей."
        else:
            logger.error(f"Ошибка HTTP {response.status_code} при получении матчей.")
            return "Ошибка при загрузке матчей. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при подключении к API HLTV: {e}")
        return "Произошла ошибка при загрузке матчей. Попробуйте позже."

# Основной обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    chat_id = update.effective_chat.id

    # Реакция на слово "погода"
    if "погода" in user_message:
        weather_info = get_weather()
        await context.bot.send_message(chat_id=chat_id, text=weather_info)
        return

    # Реакция на слова "кс", "катка" и подобные
    if any(keyword in user_message for keyword in ["катка", "кс", "cs", "будешь играть"]):
        phrases = [
            "Внимание! Настоящий задрот КС!",
            "Всем замереть! Задрот в чате!",
            "Опасность! Задрот КС в поле зрения. Срочно ищем противоядие!",
            "Эй, чемпион! Ты снова в деле? Готовься, твоя катка ждёт!",
            "Легенда КС появилась в чате! Все аплодируем! 👏",
        ]
        await context.bot.send_message(chat_id=chat_id, text=random.choice(phrases))
        return

    # Команда "гейм"
    if "гейм" in user_message:
        matches_info = get_upcoming_matches()
        await context.bot.send_message(chat_id=chat_id, text=f"🎮 Предстоящие матчи по CS2:\n\n{matches_info}")
        return

    # Команда "курс" для рыб
    if "курс" in user_message:
        rates = {fish: round(random.uniform(10, 1000), 2) for fish in ["карась", "лещ", "плотва", "тунец", "акула"]}
        rates_message = "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])
        await context.bot.send_message(chat_id=chat_id, text=f"🐟 Текущие курсы рыбешки:\n\n{rates_message}")
        return

    # Команда "биток" для криптовалют
    if "биток" in user_message:
        currency_info = get_bitcoin_and_other_currencies()
        await context.bot.send_message(chat_id=chat_id, text=currency_info)
        return

    # Команда "анекдот"
    if "анекдот" in user_message:
        joke = get_joke()
        await context.bot.send_message(chat_id=chat_id, text=joke)
        return

    # Команда "мем"
    if "мем" in user_message:
        meme_url = get_random_meme()
        if meme_url:
            await context.bot.send_photo(chat_id=chat_id, photo=meme_url)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Не удалось загрузить мем.")
        return

# Запуск бота
def main():
    print("Запуск бота...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Регистрация планировщика
    scheduler(app)

    # Запуск Flask-сервера и Telegram Polling
    keep_alive()
    Thread(target=lambda: schedule.run_pending()).start()
    app.run_polling()

if __name__ == "__main__":
    main()
