import os
import re
import asyncio
import threading
from flask import Flask

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -------------------- CONFIG --------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", "10000"))

# -------------------- FLASK (Render needs a port) --------------------
web = Flask(__name__)

@web.get("/")
def home():
    return "OK - telegram bot is running"

@web.get("/health")
def health():
    return "healthy"


# -------------------- TELEGRAM HANDLERS --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi 🤖\nSend: 168 myr 4.19 10%")


async def auto_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.lower()
    chat_type = msg.chat.type  # private / group / supergroup
    bot_username = (context.bot.username or "").lower()

    # In groups: reply ONLY if bot is mentioned
    if chat_type in ("group", "supergroup"):
        mentioned = any(
            ent.type == "mention"
            and text[ent.offset : ent.offset + ent.length] == f"@{bot_username}"
            for ent in (msg.entities or [])
        )
        if not mentioned:
            return

    # Must contain profit percent like "10%"
    m = re.search(r"(\d+\.?\d*)\s*%", text)
    if not m:
        await msg.reply_text("Missing profit %. Example: 168 myr 4.19 10%")
        return

    nums = [float(x) for x in re.findall(r"\d+\.?\d*", text)]
    if len(nums) < 2:
        await msg.reply_text("I need: amount + rate + profit%\nExample: 168 myr 4.19 10%")
        return

    myr, rate = nums[0], nums[1]
    percent = float(m.group(1))

    usd = myr / rate
    profit = usd * percent / 100

    await msg.reply_text(
        f"MYR: {myr:.2f}\n"
        f"Rate: {rate}\n"
        f"USD: {usd:.2f}\n"
        f"Your profit ({percent}%): {profit:.2f} USD"
    )


# -------------------- RUN TELEGRAM BOT (in thread) --------------------
def run_telegram_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN environment variable is missing.")
        return

    # Each thread needs its own loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_calc))

    # IMPORTANT: disable signal handlers because we're in a thread
    app.run_polling(stop_signals=None)


# -------------------- MAIN --------------------
def main():
    # Start Telegram bot in background thread
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

    # Start Flask web server (Render checks this port)
    web.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
