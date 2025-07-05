import logging
import os
from flask import Flask, request

from telegram import Update
from telegram.ext import Application

from bot import create_application

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App ---
app = Flask(__name__)
telegram_app: Application = create_application()


# --- Webhook route ---
@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)
        return "OK", 200
    except Exception as e:
        logger.exception(f"❌ Webhook error: {e}")
        return "Internal error", 500


# --- Sanity check ---
@app.route("/", methods=["GET"])
def index():
    return "✅ Bot is online — Flask is responding."


# --- Local debug mode (optional) ---
if __name__ == "__main__":
    app.run(port=8080, debug=True)
