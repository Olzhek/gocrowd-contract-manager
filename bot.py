from telegram.ext import ApplicationBuilder, CommandHandler

def setup_bot(token) :
    from contract_manager import ContractManager
    from handlers import help_command, start, summary, ask, schedule, next_payment, this_month

    app = ApplicationBuilder().token(token).build()

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

    return app