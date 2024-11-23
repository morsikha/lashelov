# -*- coding: utf-8 -*-
import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
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

# Функция проверки тревоги в Киеве (пример API)
def check_kyiv_alert():
    try:
        # Замените URL на реальное API для тревог
        response = requests.get("https://api.ukraine-alerts.example/kyiv")  # Пример URL
        if response.status_code == 200:
            data = response.json()
            return data.get("alert", False)  # Если тревога, возвращает True
    except Exception as e:
        logger.error(f"Ошибка при проверке тревоги: {e}")
    return False

# Функция отправки уведомлений в группы
async def send_alert_to_groups(app: Application):
    try:
        message = "🚨 Внимание! Воздушная тревога в Киеве! Будьте в укрытии!"
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

# Планировщик для проверки тревоги каждые 1 минуту
def scheduler(app: Application):
    schedule.every(1).minutes.do(lambda: app.create_task(send_alert_to_groups(app)))

# Функция получения погоды для Киева
def get_weather():
    city = "Kyiv"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = round(data['main']['temp'])
            description = data['weather'][0]['description']
            return f"Погода в {city}: {temp}°C, {description.capitalize()}"
        return "Не удалось получить данные о погоде."
    except Exception as e:
        logger.error(f"Ошибка при получении погоды: {e}")
        return "Произошла ошибка при загрузке данных о погоде."

# Функция получения случайного мема через API Imgflip
def get_random_meme():
    url = "https://api.imgflip.com/get_memes"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            memes = data.get("data", {}).get("memes", [])
            if memes:
                return random.choice(memes)["url"]
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении мема: {e}")
        return None

# Функция для получения анекдотов
def get_joke():
    url = "https://rozdil.lviv.ua/anekdot/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            jokes = [joke.get_text().strip() for joke in soup.find_all("a", class_="hoveranek black")]
            return random.choice(jokes) if jokes else "Анекдоты не найдены."
        return "Ошибка при получении анекдотов."
    except Exception as e:
        logger.error(f"Ошибка при получении анекдотов: {e}")
        return "Произошла ошибка при загрузке анекдотов."

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
