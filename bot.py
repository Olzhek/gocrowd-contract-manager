from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests, json, os
from contract_model import Contract
from rapidfuzz import process
from datetime import date
import locale
import pandas as pd

locale.setlocale(locale.LC_TIME, "Russian_Russia.1251")  # Windows fallback

OLLAMA_URL = "http://localhost:11434/api/generate"
# BOT_TOKEN = "7741269885:AAF8n3VrWkHYRoxCgdTtZ4rAFDjuYM9uMkU"
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CONTRACTS_PATH = os.path.join(DATA_DIR, 'contracts.json')

today = date.today().strftime("%d %B %Y")

SYSTEM_PROMPT = f"""
Today is {today}.
You are a helpful assistant that explains GoCrowd contract and payment information to the user in plain Russian. The user is a lender to companies.
- All currency is in Kazakhstani tenge (₸).
- Interest rates are annual, and should be shown as percentages, e.g. 12% годовых.
- Dates should be shown in Russian format, like "5 августа 2025".
- Do not mention internal variables like 'principal' or 'interest_rate'.
- Explain clearly as if you're speaking to a regular person, not a programmer.
- Do not refer to or describe any source code or JSON structure.
- When referring to the user, use capitalized "Вы" instead of "вы" and all the other variations like "Вам", "Ваш", etc.
"""

def load_contracts() :
    if os.path.exists(CONTRACTS_PATH) :
        with open(CONTRACTS_PATH, "r", encoding="utf-8") as f :
            return json.load(f)
    return []

def ask_ollama(user_prompt: str) :
    prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
    response = requests.post(OLLAMA_URL, json={"model": "mistral", "prompt": prompt, "stream": False})
    return response.json()["response"]

# /help handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    commands = [
        "/summary – Показать сводную информацию по контрактам",
        "/schedule – Показать график выплат по контракту",
        "/ask – Задать вопрос об одном или нескольких контрактах",
        "/next – Показать следующую выплату",
        "/thismonth – Показать все выплаты в этом месяце"
        "/help – Показать это меню"
    ]
    await update.message.reply_text("\n".join(commands))

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    await update.message.reply_text("Приветствую! Я помогу Вам разобраться с контрактами на GoCrowd. Попробуйте команду /help для информации.")

# /summary handler
# async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) :
#     await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
#     contracts = load_contracts()
#     prompt = f"""
#         Контракты включают параметр repayment_start_month — это номер месяца, начиная с которого начинается погашение основного долга.
#         До этого платятся только проценты.
#         Покажи сводную информацию по контрактам ниже.
#         {json.dumps(contracts, indent=2, ensure_ascii=False)}
#     """
#     reply = ask_ollama(prompt)
#     await update.message.reply_text(reply)

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    manager = context.bot_data["manager"]
    lines = []
    for idx, contract in enumerate(manager.contracts) :
        summ = contract.summary()
        my_date = date.fromisoformat(summ["start_date"]).strftime("%d %B %Y")
        lines.append(
            f"Контракт {idx+1}:\n"
            f"Название: {summ["name"]}\n"
            f"Основной долг: {summ["principal"]} ₸\n"
            f"Ставка: {summ["interest_rate"]*100}%\n"
            f"Срок: {summ["duration_months"]}\n"
            f"Месяц погашения основного долга: {summ["repayment_start_month"]}\n"
            f"Дата контракта: {my_date}\n"
        )

    message = "\n".join(lines)
    await update.message.reply_text(message)

# /ask handler
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    question = " ".join(context.args)
    contracts = load_contracts()
    prompt = f"{question}\n\nВот контракты:\n{json.dumps(contracts, indent=2, ensure_ascii=False)}"
    reply = ask_ollama(prompt)
    await update.message.reply_text(reply)

# /schedule <contract_name> handler
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    args = context.args
    if not args :
        await update.message.reply_text("Введите название контракта.")
        return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    contract_name = " ".join(args)
    contracts_data = load_contracts()
    contract_names = [c['name'] for c in contracts_data]

    matches = process.extractOne(contract_name, contract_names, score_cutoff=60)

    if not matches :
        await update.message.reply_text("Контракт не найден. Уточните название.")
        return
    
    best_match_name, score, idx = matches
    matched_contract_dict = contracts_data[idx]
    contract = Contract.from_dict(matched_contract_dict)
    schedule = contract.get_schedule()
    for row in schedule :
        row["date"] = row["date"].strftime("%d %B %Y")
    df = pd.DataFrame(schedule)
    text = df.to_markdown(index=False)
    prompt = f"""
        Вот график выплат по контракту "{contract.name}":

        {text}

        Выведи этот график в виде читабельного текста по пунктам БЕЗ таблицы, чтобы было комфортно прочитать на телефоне в мессенджере (Телеграм). Не сокращай дату, укажи день месяца тоже. Не пиши лишние параграфы/слова.
        Примерный формат:
        1. 1 Январа 2025 - данные
        
        2. 1 Февраля 2025 - данные
    """
    reply = ask_ollama(prompt)
    await update.message.reply_text(reply)

# /next handler
async def next_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    manager = context.bot_data["manager"]
    today = date.today()
    all_upcoming = []

    for contract in manager.contracts :
        schedule = contract.get_schedule()
        future_payments = [p for p in schedule if p["date"] >= today]

        if future_payments :
            next_pay = min(future_payments, key=lambda x: x["date"])
            all_upcoming.append((next_pay["date"], contract.name, next_pay))
    
    if not all_upcoming :
        await update.message.reply_text("Предстоящих выплат нет.")
        return
    
    all_upcoming.sort(key=lambda x: x[0])
    payment_date, contract_name, payment = all_upcoming[0]

    formatted = (
        f"Ближайшая выплата:\n"
        f"Контракт: {contract_name}\n"
        f"Дата: {payment_date.strftime('%d %B %Y')}\n"
        f"Сумма платежа: {payment['total']} ₸\n"
        f"Остаток долга: {payment['remaining_principal']} ₸\n"
    )

    await update.message.reply_text(formatted)

# /thismonth handler
async def this_month(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    today = date.today()
    current_year = today.year
    current_month = today.month

    manager = context.bot_data["manager"]
    payments_this_month = []

    for contract in manager.contracts :
        schedule = contract.get_schedule()
        for p in schedule :
            d = p["date"]
            if d.year == current_year and d.month == current_month :
                payments_this_month.append({
                    "date": d,
                    "contract": contract.name,
                    "payment": p["total"],
                    "principal": p["remaining_principal"]
                })

    if not payments_this_month :
        await update.message.reply_text("В этом месяце нет предстоящих выплат.")
        return
    
    payments_this_month.sort(key=lambda x: x["date"])

    text = "Выплаты в этом месяце:\n\n"
    for p in payments_this_month :
        text += (
            f"🔸 {p['date'].strftime('%d %B %Y')} — «{p['contract']}»\n"
            f"  💰 Платёж: {p['payment']} ₸  |  📉 Остаток долга: {p['principal']} ₸\n\n"
        )

    await update.message.reply_text(text.strip())


# Main app
if __name__ == "__main__" :
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    from contract_manager import ContractManager
    manager = ContractManager()
    manager.load_from_file()

    app.bot_data["manager"] = manager

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("next", next_payment))
    app.add_handler(CommandHandler("thismonth", this_month))

    print("Bot is running...")
    app.run_polling()