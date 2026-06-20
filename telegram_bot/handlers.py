import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List

from telegram import Update
from telegram.ext import ContextTypes

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config, load_watchlist, save_watchlist
from src.collector import StockBitCollector
from src.screener import MultiIndicatorScreener
from src.risk import PositionSizer

from formatter import (
    format_signal,
    format_analysis,
    format_signals,
    format_watchlist,
    format_market_status,
    format_risk_info,
    format_welcome,
    format_help,
    format_error,
    format_success,
    format_info,
    format_daily_summary,
)

config = load_config()
collector = StockBitCollector()
screener = MultiIndicatorScreener(config)
position_sizer = PositionSizer(config)

user_settings = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_welcome()
    await update.message.reply_text(text, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_help()
    await update.message.reply_text(text, parse_mode="HTML")


async def screen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        text = format_error("Saham tidak dispesifikasikan. Contoh: /screen BBCA")
        await update.message.reply_text(text, parse_mode="HTML")
        return

    symbols = [arg.upper() for arg in context.args]

    await update.message.reply_text(
        format_info(f"Screening {len(symbols)} saham..."),
        parse_mode="HTML",
    )

    signals = []
    for symbol in symbols:
        try:
            df = collector.get_stock_data(symbol, days=60, timeframe="15m")
            if not df.empty:
                signal = screener.screen_stock(symbol, df)
                if signal:
                    signals.append({
                        "symbol": symbol,
                        "score": signal.score,
                        "entry_price": signal.entry_price,
                        "stop_loss": signal.stop_loss,
                        "take_profit": signal.take_profit,
                        "signal_type": signal.signal_type,
                        "indicators": signal.indicators,
                    })
        except Exception as e:
            await update.message.reply_text(
                format_error(f"Error screening {symbol}: {str(e)}"),
                parse_mode="HTML",
            )

    if signals:
        for signal in signals:
            text = format_signal(signal)
            await update.message.reply_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(
            format_info("Tidak ada sinyal ditemukan"),
            parse_mode="HTML",
        )


async def screenall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    watchlist = load_watchlist()

    if not watchlist:
        await update.message.reply_text(
            format_error("Watchlist kosong. Gunakan /add untuk menambah saham."),
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        format_info(f"Screening {len(watchlist)} saham..."),
        parse_mode="HTML",
    )

    signals = []
    for symbol in watchlist:
        try:
            df = collector.get_stock_data(symbol, days=60, timeframe="15m")
            if not df.empty:
                signal = screener.screen_stock(symbol, df)
                if signal:
                    signals.append({
                        "symbol": symbol,
                        "score": signal.score,
                        "entry_price": signal.entry_price,
                        "stop_loss": signal.stop_loss,
                        "take_profit": signal.take_profit,
                        "signal_type": signal.signal_type,
                        "indicators": signal.indicators,
                    })
        except Exception:
            pass

    if signals:
        signals.sort(key=lambda x: x.get("score", 0), reverse=True)
        text = format_signals(signals)
        await update.message.reply_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(
            format_info("Tidak ada sinyal ditemukan"),
            parse_mode="HTML",
        )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            format_error("Saham tidak dispesifikasikan. Contoh: /analyze BBCA"),
            parse_mode="HTML",
        )
        return

    symbol = context.args[0].upper()

    await update.message.reply_text(
        format_info(f"Menganalisis {symbol}..."),
        parse_mode="HTML",
    )

    try:
        df = collector.get_stock_data(symbol, days=60, timeframe="15m")

        if df.empty:
            await update.message.reply_text(
                format_error(f"Tidak data ditemukan untuk {symbol}"),
                parse_mode="HTML",
            )
            return

        from src.data_models import StockData
        stock_data = StockData.from_dataframe(symbol, df)
        analysis = screener.analyze_stock(stock_data)

        text = format_analysis(analysis)
        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            format_error(f"Error: {str(e)}"),
            parse_mode="HTML",
        )


async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    watchlist = load_watchlist()
    text = format_watchlist(watchlist)
    await update.message.reply_text(text, parse_mode="HTML")


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            format_error("Saham tidak dispesifikasikan. Contoh: /add BBNI"),
            parse_mode="HTML",
        )
        return

    symbol = context.args[0].upper()
    watchlist = load_watchlist()

    if symbol in watchlist:
        await update.message.reply_text(
            format_info(f"{symbol} sudah ada di watchlist"),
            parse_mode="HTML",
        )
        return

    watchlist.append(symbol)
    save_watchlist(watchlist)

    await update.message.reply_text(
        format_success(f"{symbol} ditambahkan ke watchlist"),
        parse_mode="HTML",
    )


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            format_error("Saham tidak dispesifikasikan. Contoh: /remove BBNI"),
            parse_mode="HTML",
        )
        return

    symbol = context.args[0].upper()
    watchlist = load_watchlist()

    if symbol not in watchlist:
        await update.message.reply_text(
            format_info(f"{symbol} tidak ada di watchlist"),
            parse_mode="HTML",
        )
        return

    watchlist.remove(symbol)
    save_watchlist(watchlist)

    await update.message.reply_text(
        format_success(f"{symbol} dihapus dari watchlist"),
        parse_mode="HTML",
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = collector.get_market_status()
    text = format_market_status(status)
    await update.message.reply_text(text, parse_mode="HTML")


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    risk = position_sizer.get_risk_summary()
    text = format_risk_info(risk)
    await update.message.reply_text(text, parse_mode="HTML")


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in user_settings:
        user_settings[user_id] = {"alert_enabled": True, "interval": 15}

    if not context.args:
        current = "ON" if user_settings[user_id]["alert_enabled"] else "OFF"
        await update.message.reply_text(
            format_info(f"Auto alert saat ini: {current}"),
            parse_mode="HTML",
        )
        return

    setting = context.args[0].lower()

    if setting == "on":
        user_settings[user_id]["alert_enabled"] = True
        await update.message.reply_text(
            format_success("Auto alert diaktifkan"),
            parse_mode="HTML",
        )
    elif setting == "off":
        user_settings[user_id]["alert_enabled"] = False
        await update.message.reply_text(
            format_success("Auto alert dimatikan"),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            format_error("Pilihan: /alert on atau /alert off"),
            parse_mode="HTML",
        )


async def interval_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in user_settings:
        user_settings[user_id] = {"alert_enabled": True, "interval": 15}

    if not context.args:
        current = user_settings[user_id]["interval"]
        await update.message.reply_text(
            format_info(f"Interval saat ini: {current} menit"),
            parse_mode="HTML",
        )
        return

    try:
        interval = int(context.args[0])
        if interval < 1 or interval > 60:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            format_error("Interval harus 1-60 menit"),
            parse_mode="HTML",
        )
        return

    user_settings[user_id]["interval"] = interval
    await update.message.reply_text(
        format_success(f"Interval diatur ke {interval} menit"),
        parse_mode="HTML",
    )
