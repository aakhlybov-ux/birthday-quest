import sqlite3
import json
import asyncio
from aiogram.filters import CommandStart
from aiogram import Bot, Dispatcher, types, F

# --- КОНФИГУРАЦИЯ (Переменные прямо в файле) ---
BOT_TOKEN = '8837405019:AAFk_8uNRqGEbN936naBX3lzUSa3aEyNibU' 
GIRLFRIEND_ID = 1003574497
TARGET_ID = GIRLFRIEND_ID
ADMIN_ID = 1898915209

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_NAME = "database.db"

def init_db():
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_completed FROM user_choices WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def save_user_choices(user_id, place, time, wishes):
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

    if user_id != TARGET_ID and user_id != ADMIN_ID:
        await message.answer("🔒 Извини, этот бот создан для конкретного человека.")
        return

    is_completed = get_user_status(user_id)

    
    kb = [
        [types.KeyboardButton(
            text="Пройти опрос 🎁", 
            web_app=types.WebAppInfo(url="https://aakhlybov-ux.github.io/birthday-quest/?v=4")
        )]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )

    if not is_completed:
        await message.answer(
            f"привет, ариночка! ❤️\n\n"
            f"я приготовил для тебя кое-что особенное.\n"
            f"нажми на кнопку «Пройти опрос 🎁» внизу, чтобы начать ✨",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            f"с возвращением, солнце 🥰\n\n"
            f"я уже увидел все твои пожелания. если хочешь что-то поменять, "
            f"можешь пройти опрос заново по кнопке внизу! 🗺️",
            reply_markup=keyboard
        )


@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    user_id = message.from_user.id
    
    try:
        
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)
        
        place = data.get("place", "Не выбрано")
        time = data.get("time", "Не выбрано")
        wishes = data.get("wishes", "")
        
        
        save_user_choices(user_id, place, time, wishes)
        
        # Подтверждаем пользователю успешное заполнение квеста
        await message.answer(
            f"запомнил твои ответы, кисунь ✨\n\n"
            f"уже приступаю к подготовке нашего идеального дня 🥰"
        )

        admin_report = (
            f"🔔 **Новый отчет по квесту!** 🔔\n\n"
            f"❤️ Любимая заполнила анкету в Web App:\n\n"
            f"📍 **Выбранное место:** {place}\n"
            f"⏰ **Дата и время:** {time}\n"
            f"💌 **Пожелания:** {wishes if wishes else 'Оставлено пустым'}"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=admin_report, parse_mode="Markdown")
        
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