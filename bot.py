import aiosqlite
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DB_FILE = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT
            );
        """)
        await db.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await init_db()

    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or "пользователь"

    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()

        if result:
            await update.message.reply_text(f"С возвращением, {first_name}!\nВаш username: @{username}")
        else:
            await db.execute(
                "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username, first_name)
            )
            await db.commit()
            await update.message.reply_text(f"Привет, {first_name}! Ты успешно зарегистрирован.")

if __name__ == "__main__":
    import asyncio
    import os

    TOKEN = os.getenv("BOT_TOKEN") or "PASTE_YOUR_TOKEN_HERE"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    asyncio.run(init_db())  # Создание БД до запуска
    app.run_polling()
