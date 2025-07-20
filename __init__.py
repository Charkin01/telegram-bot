import os
import sys
import asyncio
import traceback
from flask import Flask, request
from telegram import Update

# ─── Paths ───────────────────────────────────────────────
bot_folder = os.path.join(os.path.dirname(__file__), "telegram-bot")
if bot_folder not in sys.path:
    sys.path.insert(0, bot_folder)

# ─── Import from telegram-bot/server.py ──────────────────
try:
    from server import bot_app, runner, log, status_log
except Exception as e:
    tb = traceback.format_exc()
    status_log = [f"[init-import-error] {e}", tb]
    log = lambda msg: status_log.append(msg)

# ─── Global Event Loop (shared) ──────────────────────────
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    loop.run_until_complete(runner())
    status_log.append("[init] Bot runner executed successfully")
except Exception as e:
    tb = traceback.format_exc()
    status_log.append(f"[init-runner-error] {e}")
    status_log.append(tb)

# ─── Flask App ────────────────────────────────────────────
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def debug():
    if request.method == "POST":
        try:
            headers = dict(request.headers)
            body = request.get_data(as_text=True)
            json_data = request.get_json(force=True)

            log("[flask] POST received")
            log(f"Headers: {headers}")
            log(f"Body: {body[:300]}...")

            update = Update.de_json(json_data, bot_app.bot)

            # Log user message
            if update.message:
                user = update.effective_user
                log(f"[msg] {user.first_name} (@{user.username}) → {update.message.text}")
            else:
                log("[msg] No message found in update")

            loop.run_until_complete(bot_app.process_update(update))
            log("[flask] process_update completed")
            return "ok", 200

        except Exception as e:
            tb = traceback.format_exc()
            status_log.append(f"[POST ERROR] {e}")
            status_log.append(tb)
            return f"<h3>POST ERROR</h3><pre>{tb}</pre>", 500

    return f"""
    <h3>Raw POST debug</h3>
    <pre>{chr(10).join(status_log[-25:])}</pre>
    <p>Send /start to bot and reload page</p>
    """
