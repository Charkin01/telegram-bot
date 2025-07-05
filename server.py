from flask import Flask, request
import logging
import os
from telegram import Update
from telegram.ext import Application
from bot import create_application  # You will define this in bot.py

# Optional: load .env if needed in future
# from dotenv import load_dotenv
# load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Load Telegram bot application (dispatcher, handlers etc.)
telegram_app: Application = create_application()

# Webhook route – where Telegram sends POST updates
@app.route(f"/{telegram_app.bot.token}", methods=["POST"])
async def telegram_webhook():
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)
    except Exception as e:
        logger.exception(f"❌ Error handling update: {e}")
    return "OK", 200

# Optional sanity check – useful for browser test
@app.route("/", methods=["GET"])
def root_check():
    return "✅ Flask server running — bot is online."

# Optional for manual testing
if __name__ == "__main__":
    app.run(debug=True)

