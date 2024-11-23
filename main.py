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

# Функция получения предстоящих матчей через HLTV Unofficial API
def get_upcoming_matches():
    url = "https://hltv-api.vercel.app/api/matches"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            if matches:
                upcoming_matches = []
                for match in matches[:5]:  # Получаем первые 5 матчей
                    team1 = match.get("team1", {}).get("name", "Неизвестно")
                    team2 = match.get("team2", {}).get("name", "Неизвестно")
                    time = match.get("time", "Время неизвестно")
                    tournament = match.get("event", {}).get("name", "Турнир неизвестен")
                    upcoming_matches.append(f"{team1} vs {team2}\nТурнир: {tournament}\nВремя: {time}")
                return "\n\n".join(upcoming_matches)
            else:
                return "Предстоящие матчи не найдены."
        else:
            logger.error(f"Ошибка HTTP {response.status_code} при получении матчей.")
            return "Ошибка при загрузке матчей. Попробуйте позже."
    except requests.exceptions.Timeout:
        logger.error("Превышено время ожидания при подключении к HLTV API.")
        return "Превышено время ожидания. Попробуйте позже."
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при подключении к HLTV API: {e}")
        return "Ошибка при подключении к HLTV API."
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
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

    # Команда "курс"
    if "курс" in user_message:
        rates = {fish: round(random.uniform(10, 1000), 2) for fish in ["карась", "лещ", "плотва", "тунец", "акула"]}
        rates_message = "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])
        await context.bot.send_message(chat_id=chat_id, text=f"🐟 Текущие курсы рыбешки:\n\n{rates_message}")
        return

    # Команда "биток"
    if "биток" in user_message:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            btc_price = data.get("bitcoin", {}).get("usd", "Неизвестно")
            currencies_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,ripple,cardano,solana,polkadot&vs_currencies=usd"
            currencies_response = requests.get(currencies_url)
            currencies_message = ""
            if currencies_response.status_code == 200:
                currencies_data = currencies_response.json()
                for currency, details in currencies_data.items():
                    currencies_message += f"{currency.capitalize()}: ${details['usd']}\n"
            message = f"💰 Курс биткоина: ${btc_price} USD\n\n🌍 Другие курсы:\n{currencies_message}"
            await context.bot.send_message(chat_id=chat_id, text=message)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Не удалось получить курс биткоина.")
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

    # Команда "гейм"
    if "гейм" in user_message:
        matches_info = get_upcoming_matches()
        await context.bot.send_message(chat_id=chat_id, text=f"🎮 Предстоящие матчи по CS2:\n\n{matches_info}")
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
