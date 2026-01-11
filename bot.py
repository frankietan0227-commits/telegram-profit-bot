import os
import re
import asyncio
import threading
from flask import Flask

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters


# -------------------- TELEGRAM BOT --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi 🤖\nSend: 168 myr 4.19 10%")


async def auto_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.lower()
    chat_type = msg.chat.type  # "private", "group", "supergroup"
    bot_username = (context.bot.username or "").lower()

    # In groups: reply ONLY if mentioned (no spam)
    if chat_type in ("group", "supergroup"):
        mentioned = False
        for ent in (msg.entities or []):
            if ent.type == "mention":
                mention_text = text[ent.offset : ent.offset + ent.length]
                if mention_text == f"@{bot_username}":
                    mentioned = True
                    break
        if not mentioned:
            return

    # Require % sign
    m = re.search(r"(\d+\.?\d*)\s*%", text)
    if not m:
        return

    nums = [float(x) for x in re.findall(r"\d+\.?\d*", text)]
    if len(nums) < 2:
        return

    myr = nums[0]
    rate = nums[1]
    percent = float(m.group(1))

    usd = myr / rate
    profit = usd * percent / 100

    await msg.reply_text(
        f"MYR: {myr:.2f}\n"
        f"Rate: {rate}\n"
        f"USD: {usd:.2f}\n"
        f"Your profit ({percent}%): {profit:.2f} USD"
    )


def run_telegram_bot():
    """
    Run the telegram bot in a background thread with its own event loop.
    """
    token = os.environ["BOT_TOKEN"]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_calc))

    # This blocks forever (good)
    app.run_polling()


# -------------------- WEB SERVER (for Render) --------------------

web = Flask(__name__)

@web.get("/")
def home():
    return "OK - telegram bot is running"

@web.get("/health")
def health():
    return "healthy"


def main():
    # Start Telegram bot in background
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

    # Start Web server (Render needs an open port)
    port = int(os.environ.get("PORT", "10000"))
    web.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
