from flask import Flask, request
import telegram
import os
import asyncio

from bot import setup_bot

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

app = Flask(__name__)

application = setup_bot(TOKEN)

async def process_webhook(update_data):
    await application.initialize()
    await application.bot.initialize()
    update = telegram.Update.de_json(update_data, application.bot)
    await application.process_update(update)

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook() :
    print("📩 Telegram sent an update")
    try:
        data = request.get_json(force=True)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_webhook(data))
    except Exception as e:
        print("❌ Error in webhook:", e)
    return "ok"

@app.route("/", methods=["GET"])
def health_check() :
    return "Bot is running! Final Revision!"

if __name__ == "__main__" :
    app.run(host="0.0.0.0", port=8080)