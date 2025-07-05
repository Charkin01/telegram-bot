import os
import logging
import asyncio
import aiosqlite

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# --- Config ---
DB_FILE = "users.db"
ASKING_ORG_NAME = "asking_org_name"
ASKING_ADDRESS = "asking_address"
ASKING_CONTACT = "asking_contact"

# --- Logger ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Database ---
class DatabaseManager:
    @staticmethod
    async def init_db():
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    org_name TEXT,
                    address TEXT,
                    contact TEXT,
                    state TEXT
                )
            """)
            await db.commit()

    @staticmethod
    async def get_user(user_id: int):
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return await cursor.fetchone()

    @staticmethod
    async def create_user(user_id: int, username: str, first_name: str):
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name, state) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, ASKING_ORG_NAME)
            )
            await db.commit()

    @staticmethod
    async def update_user(user_id: int, **fields):
        async with aiosqlite.connect(DB_FILE) as db:
            columns = ", ".join([f"{key} = ?" for key in fields])
            values = list(fields.values()) + [user_id]
            await db.execute(f"UPDATE users SET {columns} WHERE user_id = ?", values)
            await db.commit()


# --- Handlers ---
class BotHandlers:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await DatabaseManager.init_db()
        user_data = await DatabaseManager.get_user(user.id)

        if user_data and all(user_data[3:6]):
            org, addr, contact = user_data[3:6]
            keyboard = [["/reset"]]
            msg = (
                f"С возвращением, {user.first_name or 'пользователь'}!\n"
                f"Организация: {org}\nАдрес: {addr}\nКонтакт: {contact}\n\n"
                "Нажмите /reset для сброса."
            )
            await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        else:
            if not user_data:
                await DatabaseManager.create_user(user.id, user.username or "", user.first_name or "")
            await update.message.reply_text("Привет! Как называется ваша организация?")

    @staticmethod
    async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await DatabaseManager.update_user(
            update.effective_user.id,
            org_name=None,
            address=None,
            contact=None,
            state=ASKING_ORG_NAME
        )
        await update.message.reply_text("Данные сброшены. Как называется ваша организация?",
                                        reply_markup=ReplyKeyboardRemove())

    @staticmethod
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        user = await DatabaseManager.get_user(user_id)

        if not user or not user[6]:
            return

        state = user[6]
        flow = {
            ASKING_ORG_NAME: ("org_name", "Укажите адрес организации:", ASKING_ADDRESS),
            ASKING_ADDRESS: ("address", "Укажите контактный номер:", ASKING_CONTACT),
            ASKING_CONTACT: ("contact", "Спасибо! Регистрация завершена. Используйте /start для просмотра.", None),
        }

        if state in flow:
            field, next_msg, next_state = flow[state]
            await DatabaseManager.update_user(user_id, **{field: text, "state": next_state})
            await update.message.reply_text(next_msg)


# --- Bot factory ---
def create_application() -> Application:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("❌ BOT_TOKEN not set in environment")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", BotHandlers.start))
    app.add_handler(CommandHandler("reset", BotHandlers.reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.handle_text))

    return app


# --- Optional: run polling manually ---
if __name__ == "__main__":
    async def main():
        await DatabaseManager.init_db()
        app = create_application()
        logger.info("🤖 Bot polling started")
        await app.run_polling()

    asyncio.run(main())





'''


import os
import asyncio
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import aiosqlite
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce HTTP request logging noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Apply patch for Replit
nest_asyncio.apply()

# Constants
DB_FILE = "users.db"
ASKING_ORG_NAME = "asking_org_name"
ASKING_ADDRESS = "asking_address"
ASKING_CONTACT = "asking_contact"

class DatabaseManager:
    @staticmethod
    async def init_db():
        try:
            async with aiosqlite.connect(DB_FILE) as db:
                cursor = await db.execute("PRAGMA table_info(users)")
                columns = await cursor.fetchall()
                
                if not columns:
                    await db.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY,
                            username TEXT,
                            first_name TEXT,
                            org_name TEXT,
                            address TEXT,
                            contact TEXT,
                            state TEXT
                        );
                    """)
                else:
                    existing_columns = [col[1] for col in columns]
                    new_columns = ['org_name', 'address', 'contact', 'state']
                    for col in new_columns:
                        if col not in existing_columns:
                            await db.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
                await db.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    @staticmethod
    async def get_user(user_id: int):
        try:
            async with aiosqlite.connect(DB_FILE) as db:
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    @staticmethod
    async def update_user(user_id: int, **kwargs):
        try:
            async with aiosqlite.connect(DB_FILE) as db:
                set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
                values = list(kwargs.values()) + [user_id]
                await db.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")

    @staticmethod
    async def create_user(user_id: int, username: str, first_name: str):
        try:
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute(
                    "INSERT INTO users (user_id, username, first_name, state) VALUES (?, ?, ?, ?)",
                    (user_id, username, first_name, ASKING_ORG_NAME))
                await db.commit()
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")

class BotHandlers:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        username = user.username or ""
        first_name = user.first_name or "пользователь"

        result = await DatabaseManager.get_user(user_id)

        if result and all([result[3], result[4], result[5]]):  # All fields filled
            org_name, address, contact = result[3], result[4], result[5]
            keyboard = [["/reset"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                f"С возвращением, {first_name}!\n"
                f"Ваша организация: {org_name}\n"
                f"Адрес: {address}\n"
                f"Контакт: {contact}\n\n"
                "Для сброса данных нажмите /reset",
                reply_markup=reply_markup
            )
        else:
            if result:  # User exists but has empty fields
                await DatabaseManager.update_user(user_id, state=ASKING_ORG_NAME)
            else:  # New user
                await DatabaseManager.create_user(user_id, username, first_name)
            
            await update.message.reply_text(
                f"Привет, {first_name}! Давайте познакомимся.\n"
                "Как называется ваша организация?"
            )

    @staticmethod
    async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        first_name = update.effective_user.first_name or "пользователь"

        await DatabaseManager.update_user(
            user_id, 
            org_name=None, 
            address=None, 
            contact=None, 
            state=ASKING_ORG_NAME
        )
        
        await update.message.reply_text(
            f"{first_name}, ваши данные сброшены.\n"
            "Давайте заполним их заново.\n\n"
            "Как называется ваша организация?",
            reply_markup=ReplyKeyboardRemove()
        )

    @staticmethod
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text

        result = await DatabaseManager.get_user(user_id)
        if not result or not result[6]:  # No state
            return

        state = result[6]
        state_handlers = {
            ASKING_ORG_NAME: ("org_name", "Отлично! Теперь укажите адрес организации:", ASKING_ADDRESS),
            ASKING_ADDRESS: ("address", "Хорошо! Укажите контактный номер:", ASKING_CONTACT),
            ASKING_CONTACT: ("contact", "Спасибо! Регистрация завершена.\nИспользуйте /start чтобы увидеть сохраненную информацию.", None)
        }

        if state in state_handlers:
            field, message, next_state = state_handlers[state]
            await DatabaseManager.update_user(user_id, **{field: text, 'state': next_state})
            await update.message.reply_text(message)

async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return

    await DatabaseManager.init_db()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", BotHandlers.start))
    app.add_handler(CommandHandler("reset", BotHandlers.reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.handle_text))
    
    logger.info("✅ Bot started and waiting for commands...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())


 '''