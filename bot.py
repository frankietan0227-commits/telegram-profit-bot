import re
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi 🤖\nSend: 168 myr 4.19 10%")



async def auto_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.lower()
    chat_type = msg.chat.type  # "private", "group", "supergroup"

    bot_username = (context.bot.username or "").lower()

    # ✅ GROUP RULE: reply ONLY when mentioned
    if chat_type in ("group", "supergroup"):
        mentioned = False
        for ent in (msg.entities or []):
            if ent.type == "mention":
                mention_text = text[ent.offset : ent.offset + ent.length]
                if mention_text == f"@{bot_username}":
                    mentioned = True
                    break
        if not mentioned:
            return  # ignore everything else in group

    # ✅ Require % (prevents random replies)
    m = re.search(r"(\d+\.?\d*)\s*%", text)
    if not m:
        return

    # Get first 2 numbers: MYR and rate
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



def main():
    # ✅ Python 3.14: create & set event loop (fixes telegram library loop issues)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    TOKEN = "8199918990:AAEKThoG-duktPG6w6J_UUOMOzIDXCj3cjY"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_calc))

    app.run_polling()



if __name__ == "__main__":
    main()
