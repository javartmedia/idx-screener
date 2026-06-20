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
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from telegram_bot_config import BOT_TOKEN, TRADING_HOURS_START, TRADING_HOURS_END, TIMEZONE
from handlers import (
    start_command,
    help_command,
    getchatid_command,
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
    predict_command,
    predictall_command,
    upload_command,
    intraday_command,
    intraday_scan_command,
    button_callback,
    handle_message,
    error_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


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
    application.add_handler(CommandHandler("getchatid", getchatid_command))
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
    application.add_handler(CommandHandler("predict", predict_command))
    application.add_handler(CommandHandler("predictall", predictall_command))
    application.add_handler(CommandHandler("upload", upload_command))
    application.add_handler(CommandHandler("deploy", upload_command))
    application.add_handler(CommandHandler("intraday", intraday_command))
    application.add_handler(CommandHandler("intradayscan", intraday_scan_command))

    application.add_handler(CallbackQueryHandler(button_callback))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.add_error_handler(error_handler)

    print("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
