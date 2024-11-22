# -*- coding: utf-8 -*-
import os
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
import openai

# Получение API ключа
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("API-ключ OpenAI отсутствует. Проверьте файл секретов или переменную окружения.")
    raise ValueError("API-ключ OpenAI не найден. Убедитесь, что он правильно настроен.")
else:
    logging.info(f"API-ключ успешно загружен: {OPENAI_API_KEY[:5]}...")

# Проверка доступности OpenAI API
try:
    openai.api_key = OPENAI_API_KEY
    openai.Model.list()  # Тестовый запрос для проверки
    logging.info("Успешно подключено к OpenAI API.")
except Exception as e:
    logging.error(f"Ошибка подключения к OpenAI API: {e}")
    raise e

# Функция для обращения к OpenAI
def ask_openai(prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # Используйте нужный движок
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response["choices"][0]["text"].strip()
    except openai.error.AuthenticationError:
        logging.error("Ошибка аутентификации. Проверьте API-ключ OpenAI.")
        return "Ошибка аутентификации. Пожалуйста, проверьте ваш API-ключ."
    except openai.error.RateLimitError:
        logging.error("Превышен лимит запросов к OpenAI API.")
        return "Превышен лимит запросов. Пожалуйста, попробуйте позже."
    except openai.error.OpenAIError as e:
        logging.error(f"Ошибка OpenAI API: {e}")
        return "Произошла ошибка при работе с OpenAI API. Попробуйте позже."
    except Exception as e:
        logging.error(f"Непредвиденная ошибка: {e}")
        return "Произошла неизвестная ошибка. Попробуйте позже."

# Вставьте ваш токен бота
TELEGRAM_TOKEN = "7861495333:AAGb8W-B4nFg0cM8cnmLJRCbLcTpG5yQxWI"

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

# Проверка тревоги в Киеве
def check_kyiv_alert():
    url = 'https://map.ukrainealarm.com/'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            kyiv_status = soup.find('div', class_='Kyiv')
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
            app.create_task(send_alert_message(chat_id))

    schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Получение случайного мема через API Imgflip
def get_random_meme():
    url = "https://api.imgflip.com/get_memes"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            memes = data.get("data", {}).get("memes", [])
            if memes:
                random_meme = random.choice(memes)
                return random_meme["url"]
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении мема: {e}")
        return None

# Основной обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    chat_id = update.effective_chat.id
    
    # Реакция на упоминание "бот" с использованием OpenAI
    if "бот" in user_message:
        ai_response = ask_openai(f"Пользователь спросил: {user_message}")
        await context.bot.send_message(chat_id=chat_id, text=ai_response)
        return

    # Реакция на слова "кс", "каточка" и подобные
    if any(keyword in user_message for keyword in ["катка", "катку", "каточку", "кс", "cs", "будешь играть"]):
        phrases = [
            "Внимание, внимание! Смотрите сюда: перед вами настоящий задрот КС в своём естественном ареале!",
            "Всем замереть! Перед нами настоящий король каток и задротства!",
            "ТЫ че кс говнецо!"
            "На бутылку сядешь если много будешь играть в кс"
            "ты че удали кс, а то пацаны на бутылку посядят"
            "бутылка тебя ждет"
            # Другие фразы...
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
elif "биток" in user_message:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        btc_price = data.get("bitcoin", {}).get("usd", "Неизвестно")
        
        # Получение курсов других валют
        currencies_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,ripple,cardano,solana,polkadot&vs_currencies=usd"
        currencies_response = requests.get(currencies_url)
        currencies_message = ""
        
        if currencies_response.status_code == 200:
            currencies_data = currencies_response.json()
            for currency, details in currencies_data.items():
                currencies_message += f"{currency.capitalize()}: ${details['usd']}\n"
        
        # Формирование ответа
        message = f"💰 Курс биткоина: ${btc_price} USD\n\n🌍 Другие курсы:\n{currencies_message}"
        await context.bot.send_message(chat_id=chat_id, text=message)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Не удалось получить курс биткоина.")
    return

    # Команда "мем"
    elif "мем" in user_message:
        meme_url = get_random_meme()
        if meme_url:
            await context.bot.send_photo(chat_id=chat_id, photo=meme_url)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Не удалось загрузить мем.")
        return

# Объявляем функцию debug_update до её использования
async def debug_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Отладочное сообщение: {update}")
    user_message = update.message.text.lower()
    logger.info(f"Получено сообщение: {user_message}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Сообщение получено и обработано.")

def main():
    print("Запуск бота...")
    global app
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавление обработчиков
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    app.add_handler(text_handler)

    debug_handler = MessageHandler(filters.ALL, debug_update)
    app.add_handler(debug_handler)

    # Планировщик в отдельном потоке
    scheduler_thread = Thread(target=start_scheduler, args=(None,))
    scheduler_thread.start()

    # Запуск Flask-сервера и Telegram бота
    keep_alive()
    app.run_polling()

if __name__ == "__main__":
    main()
