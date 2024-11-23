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

# Переменные окружения (на Render они настраиваются в Dashboard)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Telegram Token
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # OpenWeather API Key
ALERT_IMAGE_URL = "https://raw.githubusercontent.com/ваш-репозиторий/alert.jpg"  # Замените на реальную ссылку

# Логирование
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

# Функция для планировщика (для выполнения задач в фоновом режиме)
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

# Функция получения курса криптовалют
def get_bitcoin_and_other_currencies():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,ripple,cardano,solana&vs_currencies=usd"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return "\n".join([f"{coin.capitalize()}: ${price['usd']}" for coin, price in data.items()])
        else:
            logger.error(f"HTTP {response.status_code} при обращении к CoinGecko API.")
            return "Ошибка при получении курсов криптовалют. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при получении курсов криптовалют: {e}")
        return "Произошла ошибка при загрузке курсов. Попробуйте позже."

# Функция получения анекдотов
def get_joke():
    url = "https://rozdil.lviv.ua/anekdot/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            jokes = [joke.get_text().strip() for joke in soup.find_all("a", class_="hoveranek black")]
            if jokes:
                return random.choice(jokes)
            else:
                logger.error("Не удалось найти анекдоты на странице.")
                return "Анекдоты временно недоступны."
        else:
            logger.error(f"Ошибка HTTP {response.status_code} при получении анекдотов.")
            return "Ошибка при загрузке анекдотов. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при подключении к сайту анекдотов: {e}")
        return "Произошла ошибка при загрузке анекдотов. Попробуйте позже."

# Функция получения погоды для Киева
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
        else:
            logger.error(f"HTTP {response.status_code} при загрузке погоды.")
            return "Не удалось получить данные о погоде."
    except Exception as e:
        logger.error(f"Ошибка при получении погоды: {e}")
        return "Произошла ошибка при загрузке данных о погоде."

# Функция получения случайного мема через API Imgflip
def get_random_meme():
    url = "https://api.imgflip.com/get_memes"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            memes = data.get("data", {}).get("memes", [])
            return random.choice(memes)["url"] if memes else "Не удалось найти мемы."
        else:
            logger.error(f"HTTP {response.status_code} при загрузке мемов.")
            return "Ошибка при загрузке мемов. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при загрузке мемов: {e}")
        return "Произошла ошибка при загрузке мемов. Попробуйте позже."

# Функция получения матчей CS2
def get_upcoming_matches():
    url = "https://hltv-api.vercel.app/api/matches"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            matches = response.json()
            if matches and isinstance(matches, list):
                upcoming_matches = []
                for match in matches[:10]:  # Ограничиваем до 10 матчей
                    match_time = match.get("time", "Неизвестное время")
                    teams = match.get("teams", [])
                    if not teams:
                        continue
                    team_names = " vs ".join([team.get("name", "Unknown") for team in teams])
                    upcoming_matches.append(f"{match_time}: {team_names}")
                if upcoming_matches:
                    return "\n".join(upcoming_matches)
                else:
                    logger.error("HLTV API вернул данные, но матчей не найдено.")
                    return "Нет ближайших матчей."
            else:
                logger.error("HLTV API вернул некорректные данные.")
                return "Ошибка при загрузке матчей. Попробуйте позже."
        else:
            logger.error(f"HTTP {response.status_code} при загрузке матчей.")
            return "Ошибка при загрузке матчей. Попробуйте позже."
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при подключении к HLTV API: {e}")
        return "Произошла ошибка при загрузке матчей. Попробуйте позже."
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

    # Реакция на слова "кс", "катка"
    if any(keyword in user_message for keyword in ["катка", "кс", "cs", "будешь играть"]):
        phrases = [
            "Внимание! Настоящий задрот КС!",
            "Эй, чемпион! Твоя катка ждет!",
        ]
        await context.bot.send_message(chat_id=chat_id, text=random.choice(phrases))
        return

    # Команда "гейм"
    if "гейм" in user_message:
        matches_info = get_upcoming_matches()
        await context.bot.send_message(chat_id=chat_id, text=f"🎮 Матчи по CS2:\n\n{matches_info}")
        return

    # Команда "курс"
    if "курс" in user_message:
        rates = {fish: round(random.uniform(10, 1000), 2) for fish in ["карась", "лещ", "плотва", "тунец", "акула"]}
        rates_message = "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])
        await context.bot.send_message(chat_id=chat_id, text=f"🐟 Курсы рыб:\n\n{rates_message}")
        return

    # Команда "биток"
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
