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

# Настройка OpenAI API
OPENAI_API_KEY = "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"  # Вставьте свой API-ключ
openai.api_key = OPENAI_API_KEY

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
    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenAI API: {e}")
        return "Простите, я сейчас не могу ответить."

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

   # Реакция на тему CS или игр
    if any(keyword in user_message for keyword in ["катка", "катку", "каточку", "кс", "cs", "будешь играть"]):
        phrases = [
        "Внимание, внимание! Смотрите сюда: перед вами настоящий задрот КС в своём естественном ареале!",
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
        "Профессионал CS:GO уже здесь! Всем приветствовать короля каток!"
        ]
        await context.bot.send_message(chat_id=chat_id, text=random.choice(phrases))
        return

    # Реакция на упоминание "лящелов", "лящ" или "бот"
    if any(keyword in user_message for keyword in ["лящелов", "лящ", "бот"]):
        phrases = [
        "Да-да, я тут!",
        "Чего хочешь?",
        "Я не понял, это ко мне?",
        "Эй, я занят!",
        "Кто звал легенду?",
        "Здесь, чтобы спасти день! Или нет...",
        "Не мешай, я обдумываю смысл жизни.",
        "Ля, зачем меня беспокоить? 😒",
        "Угадайте, кто пришёл? Это я!",
        "Ты снова меня тревожишь?",
        "Если это не про лещей, то я ухожу.",
        "Даже в отпуске меня нашли...",
        "Я бот, а ты человек. Где справедливость?",
        "К вашим услугам, повелитель лещей!",
        "Моё присутствие делает этот чат лучше.",
        "А я думал, вы без меня не соскучитесь. 😏",
        "Что случилось? Лещи не ловятся?",
        "Говорят, меня тут обсуждали?",
        "Кто-то звал леща? Я тут.",
        "Я только зашёл на кофе... Что надо?"
        ]
        await context.bot.send_message(chat_id=chat_id, text=random.choice(phrases))
        return  # Завершаем обработку, чтобы не выполнять другие условия


    if "курс" in user_message:
        rates = {fish: round(random.uniform(10, 1000), 2) for fish in ["карась", "лещ", "плотва", "тунец", "акула"]}
        rates_message = "\n".join([f"{fish.capitalize()}: {rate} грн" for fish, rate in rates.items()])
        await context.bot.send_message(chat_id=chat_id, text=f"🐟 Текущие курсы рыбешки:\n\n{rates_message}")

    elif "биток" in user_message:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            btc_price = data.get("bitcoin", {}).get("usd", "Неизвестно")
            
            # Получение курсов случайных валют
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
        meme_url = get_random_meme()
        if meme_url:
            await context.bot.send_photo(chat_id=chat_id, photo=meme_url)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Не удалось загрузить мем.")

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
