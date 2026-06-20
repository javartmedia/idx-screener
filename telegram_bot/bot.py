import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from telegram_bot_config import BOT_TOKEN, TRADING_HOURS_START, TRADING_HOURS_END, TIMEZONE
from handlers import (
    start_command,
    help_command,
    screen_command,
    screenall_command,
    analyze_command,
    watchlist_command,
    add_command,
    remove_command,
    status_command,
    risk_command,
    alert_command,
    interval_command,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text.startswith("/screen "):
        args = text.replace("/screen ", "").split()
        context.args = args
        await screen_command(update, context)
    elif text.startswith("/analyze "):
        args = text.replace("/analyze ", "").split()
        context.args = args
        await analyze_command(update, context)
    elif text.startswith("/add "):
        args = text.replace("/add ", "").split()
        context.args = args
        await add_command(update, context)
    elif text.startswith("/remove "):
        args = text.replace("/remove ", "").split()
        context.args = args
        await remove_command(update, context)
    elif text.startswith("/s "):
        args = text.replace("/s ", "").split()
        context.args = args
        await screen_command(update, context)
    elif text.startswith("/a "):
        args = text.replace("/a ", "").split()
        context.args = args
        await analyze_command(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")


def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not set. Please set it in .env file.")
        print("Get token from @BotFather on Telegram.")
        return

    print("Starting IDX Screener Bot...")
    print(f"Trading Hours: {TRADING_HOURS_START} - {TRADING_HOURS_END}")
    print(f"Timezone: {TIMEZONE}")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("screen", screen_command))
    application.add_handler(CommandHandler("screenall", screenall_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("watchlist", watchlist_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("remove", remove_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("risk", risk_command))
    application.add_handler(CommandHandler("alert", alert_command))
    application.add_handler(CommandHandler("interval", interval_command))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.add_error_handler(error_handler)

    print("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
