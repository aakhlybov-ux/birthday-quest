import sqlite3
import json
import asyncio

from aiogram.filters import CommandStart
from aiogram import Bot, Dispatcher, types, F

# --- КОНФИГУРАЦИЯ (Переменные прямо в файле) ---
BOT_TOKEN = '8837405019:AAFk_8uNRqGEbN936naBX3lzUSa3aEyNibU' 
GIRLFRIEND_ID = 1003574497
TARGET_ID = 1898915209

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_NAME = "database.db"

def init_db():
    """Создает базу данных и таблицу для хранения выбора, если их нет"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_choices (
            user_id INTEGER PRIMARY KEY,
            place TEXT,
            time TEXT,
            wishes TEXT,
            is_completed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_user_status(user_id):
    """Проверяет статус прохождения опроса (1 - пройдено, 0 - нет)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_completed FROM user_choices WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def save_user_choices(user_id, place, time, wishes):
    """Записывает ответы в базу данных и ставит статус прохождения 1"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_choices (user_id, place, time, wishes, is_completed)
        VALUES (?, ?, ?, ?, 1)
    ''', (user_id, place, time, wishes))
    conn.commit()
    conn.close()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    if user_id != TARGET_ID:
        await message.answer("🔒 Извини, этот бот создан для конкретного человека.")
        return

    is_completed = get_user_status(user_id)

    # Создаем обычную кнопку под полем ввода, которая на 100% поддерживает tg.sendData()
    kb = [
        [types.KeyboardButton(
            text="Пройти опрос 🎁", 
            web_app=types.WebAppInfo(url="https://aakhlybov-ux.github.io/birthday-quest/?v=5")
        )]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )

    if not is_completed:
        await message.answer(
            f"Привет, {message.from_user.first_name}! ❤️\n\n"
            f"Я приготовил для тебя кое-что очень особенное.\n"
            f"Нажми на кнопку «Пройти опрос 🎁» внизу, чтобы начать! ✨",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            f"С возвращением, солнце! 🥰\n\n"
            f"Все твои пожелания уже сохранены. Если хочешь что-то изменить, "
            f"можешь пройти опрос заново по кнопке внизу! 🗺️",
            reply_markup=keyboard
        )

# ХЭНДЛЕР ДЛЯ ПОЛУЧЕНИЯ ДАННЫХ ИЗ WEB APP
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    user_id = message.from_user.id
    
    try:
        # Извлекаем сырую строку JSON из Web App и парсим её в питоновский словарь
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)
        
        place = data.get("place", "Не выбрано")
        time = data.get("time", "Не выбрано")
        wishes = data.get("wishes", "")
        
        # Записываем всё в SQLite базу данных
        save_user_choices(user_id, place, time, wishes)
        
        # Подтверждаем пользователю успешное заполнение квеста
        await message.answer(
            f"✨ Ура! Твои ответы успешно сохранены в базу! ✨\n\n"
            f"📍 Место: {place}\n"
            f"⏰ Время: {time}\n"
            f"💌 Пожелания: {wishes if wishes else 'Без особых пожеланий'}\n\n"
            f"Я уже приступаю к подготовке нашего идеального дня! 🥰"
        )
        
    except Exception as e:
        print(f"Ошибка при обработке данных Web App: {e}")
        await message.answer("❌ Произошла ошибка при сохранении данных. Попробуй ещё раз.")

async def main():
    init_db()
    print("Бот успешно запущен, база данных готова!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())