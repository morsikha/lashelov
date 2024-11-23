# -*- coding: utf-8 -*-
import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread
import schedule

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

# Функция для отправки тревоги
async def send_alert_to_groups(app):
    try:
        message = "🚨 Увага! летит якась какашка!"
        async with app.bot:
            updates = await app.bot.get_updates()
            for update in updates:
                if update.message and update.message.chat.type in ["group", "supergroup"]:
                    chat_id = update.message.chat.id
                    await app.bot.send_message(chat_id=chat_id, text=message)
                    await app.bot.send_photo(chat_id=chat_id, photo=ALERT_IMAGE_URL)
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений: {e}")

def scheduler(app):
    schedule.every(1).minutes.do(lambda: app.create_task(send_alert_to_groups(app)))

# Получение курса криптовалют
def get_bitcoin_and_other_currencies():
    try:
        btc_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        btc_response = requests.get(btc_url).json()
        btc_price = btc_response.get("bitcoin", {}).get("usd", "Неизвестно")
        
        currencies_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,ripple,cardano,solana,polkadot&vs_currencies=usd"
        currencies_response = requests.get(currencies_url).json()
        
        currencies_message = "\n".join([f"{currency.capitalize()}: ${details['usd']}" for currency, details in currencies_response.items()])
        return f"💰 Курс биткоина: ${btc_price} USD\n\n🌍 Другие курсы:\n{currencies_message}"
    except Exception as e:
        logger.error(f"Ошибка при получении курса валют: {e}")
        return "Ошибка при загрузке курсов. Попробуйте позже."

# Случайный курс рыбы
def get_fish_rates():
    rates = {fish: round(random.uniform(10, 1000), 2) for fish in ["карась", "лещ", "плотва", "тунец", "акула"]}
    return "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])

# Получение анекдотов
def get_joke():
    url = "https://rozdil.lviv.ua/anekdot/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            jokes = [joke.get_text().strip() for joke in soup.find_all("a", class_="hoveranek black")]
            return random.choice(jokes) if jokes else "Анекдоты временно недоступны."
        return "Ошибка при загрузке анекдотов."
    except Exception as e:
        logger.error(f"Ошибка при загрузке анекдотов: {e}")
        return "Произошла ошибка при загрузке анекдотов. Попробуйте позже."

# Получение погоды в Киеве
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

# Получение мема через API Imgflip
def get_random_meme():
    url = "https://api.imgflip.com/get_memes"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            memes = response.json().get("data", {}).get("memes", [])
            return random.choice(memes)["url"] if memes else None
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении мема: {e}")
        return None

# Получение предстоящих матчей CS2
def get_upcoming_matches():
    url = "https://hltv-api.vercel.app/api/matches"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            matches = response.json()
            return "\n".join([f"{match['time']}: {', '.join([team['name'] for team in match['teams']])}" for match in matches[:10]])
        return "Нет ближайших матчей."
    except Exception as e:
        logger.error(f"Ошибка при загрузке матчей: {e}")
        return "Произошла ошибка при загрузке матчей."

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    chat_id = update.effective_chat.id

    if "погода" in user_message:
        await context.bot.send_message(chat_id, get_weather())
    elif "кс" in user_message or "катка" in user_message:
        phrases = ["Снова задрот в деле! 🎮", "Готовься к битве! 🔥"]
        await context.bot.send_message(chat_id, random.choice(phrases))
    elif "гейм" in user_message:
        await context.bot.send_message(chat_id, get_upcoming_matches())
    elif "биток" in user_message:
        await context.bot.send_message(chat_id, get_bitcoin_and_other_currencies())
    elif "курс" in user_message:
        await context.bot.send_message(chat_id, f"🐟 Курсы рыбешки:\n\n{get_fish_rates()}")
    elif "анекдот" in user_message:
        await context.bot.send_message(chat_id, get_joke())
    elif "мем" in user_message:
        meme_url = get_random_meme()
        if meme_url:
            await context.bot.send_photo(chat_id, meme_url)
        else:
            await context.bot.send_message(chat_id, "Не удалось загрузить мем.")

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
