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
import openai.error

# Получение API ключа
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("API-ключ OpenAI отсутствует. Проверьте файл секретов или переменную окружения.")
    raise ValueError("API-ключ OpenAI не найден. Убедитесь, что он правильно настроен.")
else:
    logging.info(f"API-ключ успешно загружен: {OPENAI_API_KEY[:5]}...")

# Установка API ключа
openai.api_key = OPENAI_API_KEY

# Функция для обращения к OpenAI
def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты - умный помощник."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message["content"].strip()
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

    # Реакция на упоминание "бот" с использованием OpenAI
    if "бот" in user_message:
        ai_response = ask_openai(f"Пользователь спросил: {user_message}")
        await context.bot.send_message(chat_id=chat_id, text=ai_response)
        return

    # Реакция на слова "кс", "катка" и подобные
    if any(keyword in user_message for keyword in ["катка", "кс", "cs", "будешь играть"]):
        phrases = [
            "Внимание! Настоящий задрот КС!",
            "Всем замереть! Задрот в чате!",
            "Всем замереть! Перед нами настоящий король каток и задротства!",
            "Опасность! Задрот КС в поле зрения. Срочно ищем противоядие!",
            "Эй, чемпион! Ты снова в деле? Готовься, твоя катка ждёт!",
            "Легенда КС появилась в чате! Все аплодируем! 👏",
            "Кто-то сказал 'катка'? Задрот уже готов затащить! 🎮",
            "Алло, служба поддержки игр? У нас тут профессионал КС разгуливает!",
            "Это что, чемпионат мира по задротству? Прямо здесь и сейчас? 🔥",
            "Ну всё, кто-то снова готов ломать клавиатуры и мышки в КС!",
            "Смотрите на этого бойца! С ним не поспоришь — мастер всех каток.",
            "Перед вами игрок уровня 'задрот PRO'. Бойтесь и уважайте!",
            "Задрот КС замечен! Всем срочно на позиции! 🛡️",
            "ВНИМАНИЕ! Геймер 99-го уровня вошёл в чат.",
            "Ну что, начнётся эпическая катка или опять просто разговоры? 🎧",
            "Собрались, катку делаем! Задрот уже разогревает руки!",
            "Тут запахло каткой! Готовимся наблюдать профессиональный гейминг.",
            "Ты снова в деле? Катки зовут, а ты лучший в этом деле!",
            "Перед нами мастер КС, тащит всех и вся. Мы не достойны. 🙌",
            "Это птица? Это самолёт? Нет, это задрот КС! 🚀",
            "Ты че, КС говно!",
            "На бутылку сядешь, если будешь много играть!",
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
    global app
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    keep_alive()
    app.run_polling()

if __name__ == "__main__":
    main()
