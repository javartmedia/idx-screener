import sys
import subprocess
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
    format_price_prediction,
    format_volume_analysis,
    format_prediction_menu,
    format_predict_result_menu,
    get_main_menu,
    get_screen_result_menu,
    get_back_menu,
    get_alert_menu,
)

config = load_config()
collector = StockBitCollector()
screener = MultiIndicatorScreener(config)
position_sizer = PositionSizer(config)

from src.indicators.prediction import PredictionIndicator
from src.indicators.volume_analysis import VolumeAnalysis

prediction_indicator = PredictionIndicator()
volume_analyzer = VolumeAnalysis()

user_settings = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_welcome()
    keyboard = get_main_menu()
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_help()
    keyboard = get_back_menu()
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def screen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        text = "Ketik kode saham (contoh: BBCA TLKM BBRI):"
        await update.message.reply_text(text)
        context.user_data["state"] = "waiting_screen"
        return

    symbols = [arg.upper() for arg in context.args]
    await process_screen(update, context, symbols)


async def process_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: List[str]):
    await update.message.reply_text(format_info(f"Screening {len(symbols)} saham..."), parse_mode="HTML")

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
            await update.message.reply_text(format_error(f"Error screening {symbol}: {str(e)}"), parse_mode="HTML")

    if signals:
        for signal in signals:
            text = format_signal(signal)
            keyboard = get_screen_result_menu()
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        keyboard = get_screen_result_menu()
        await update.message.reply_text(format_info("Tidak ada sinyal ditemukan"), parse_mode="HTML", reply_markup=keyboard)


async def screenall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    watchlist = load_watchlist()

    if not watchlist:
        keyboard = get_main_menu()
        await update.message.reply_text(format_error("Watchlist kosong."), parse_mode="HTML", reply_markup=keyboard)
        return

    await update.message.reply_text(format_info(f"Screening {len(watchlist)} saham..."), parse_mode="HTML")

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
        keyboard = get_screen_result_menu()
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        keyboard = get_screen_result_menu()
        await update.message.reply_text(format_info("Tidak ada sinyal ditemukan"), parse_mode="HTML", reply_markup=keyboard)


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        text = "Ketik kode saham untuk dianalisis:"
        await update.message.reply_text(text)
        context.user_data["state"] = "waiting_analyze"
        return

    symbol = context.args[0].upper()
    await process_analyze(update, context, symbol)


async def process_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
    await update.message.reply_text(format_info(f"Menganalisis {symbol}..."), parse_mode="HTML")

    try:
        df = collector.get_stock_data(symbol, days=60, timeframe="15m")

        if df.empty:
            keyboard = get_main_menu()
            await update.message.reply_text(format_error(f"Tidak data ditemukan untuk {symbol}"), parse_mode="HTML", reply_markup=keyboard)
            return

        from src.data_models import StockData
        stock_data = StockData.from_dataframe(symbol, df)
        analysis = screener.analyze_stock(stock_data)

        text = format_analysis(analysis)
        keyboard = get_back_menu()
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        await update.message.reply_text(format_error(f"Error: {str(e)}"), parse_mode="HTML")


async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    watchlist = load_watchlist()
    text = format_watchlist(watchlist)
    keyboard = get_main_menu()
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        text = "Ketik kode saham yang ingin ditambahkan:"
        await update.message.reply_text(text)
        context.user_data["state"] = "waiting_add"
        return

    symbol = context.args[0].upper()
    watchlist = load_watchlist()

    if symbol in watchlist:
        keyboard = get_main_menu()
        await update.message.reply_text(format_info(f"{symbol} sudah ada di watchlist"), parse_mode="HTML", reply_markup=keyboard)
        return

    watchlist.append(symbol)
    save_watchlist(watchlist)

    keyboard = get_main_menu()
    await update.message.reply_text(format_success(f"{symbol} ditambahkan ke watchlist"), parse_mode="HTML", reply_markup=keyboard)


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        text = "Ketik kode saham yang ingin dihapus:"
        await update.message.reply_text(text)
        context.user_data["state"] = "waiting_remove"
        return

    symbol = context.args[0].upper()
    watchlist = load_watchlist()

    if symbol not in watchlist:
        keyboard = get_main_menu()
        await update.message.reply_text(format_info(f"{symbol} tidak ada di watchlist"), parse_mode="HTML", reply_markup=keyboard)
        return

    watchlist.remove(symbol)
    save_watchlist(watchlist)

    keyboard = get_main_menu()
    await update.message.reply_text(format_success(f"{symbol} dihapus dari watchlist"), parse_mode="HTML", reply_markup=keyboard)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = collector.get_market_status()
    text = format_market_status(status)
    keyboard = get_main_menu()
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    risk = position_sizer.get_risk_summary()
    text = format_risk_info(risk)
    keyboard = get_main_menu()
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in user_settings:
        user_settings[user_id] = {"alert_enabled": True, "interval": 15}

    is_on = user_settings[user_id]["alert_enabled"]
    status = "ON" if is_on else "OFF"
    text = f"<b>Auto Alert:</b> {status}"
    keyboard = get_alert_menu(is_on)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def alert_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {"alert_enabled": True, "interval": 15}
    user_settings[user_id]["alert_enabled"] = True

    text = "<b>Auto Alert:</b> ON"
    keyboard = get_alert_menu(True)
    await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


async def alert_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {"alert_enabled": True, "interval": 15}
    user_settings[user_id]["alert_enabled"] = False

    text = "<b>Auto Alert:</b> OFF"
    keyboard = get_alert_menu(False)
    await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


async def interval_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in user_settings:
        user_settings[user_id] = {"alert_enabled": True, "interval": 15}

    if not context.args:
        current = user_settings[user_id]["interval"]
        await update.message.reply_text(format_info(f"Interval saat ini: {current} menit"), parse_mode="HTML")
        return

    try:
        interval = int(context.args[0])
        if interval < 1 or interval > 60:
            raise ValueError
    except ValueError:
        await update.message.reply_text(format_error("Interval harus 1-60 menit"), parse_mode="HTML")
        return

    user_settings[user_id]["interval"] = interval
    await update.message.reply_text(format_success(f"Interval diatur ke {interval} menit"), parse_mode="HTML")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {"alert_enabled": True, "interval": 15}

    settings = user_settings[user_id]
    text = f"""
<b>Settings</b>

<b>Auto Alert:</b> {'ON' if settings['alert_enabled'] else 'OFF'}
<b>Interval:</b> {settings['interval']} menit
"""
    keyboard = get_main_menu()
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        text = "Ketik kode saham untuk prediksi (contoh: BBCA):"
        await update.message.reply_text(text)
        context.user_data["state"] = "waiting_predict"
        return

    symbol = context.args[0].upper()
    await process_predict(update, context, symbol)


async def process_predict(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
    await update.message.reply_text(format_info(f"Menganalisis {symbol} untuk prediksi..."), parse_mode="HTML")

    try:
        df = collector.get_stock_data(symbol, days=60, timeframe="15m")

        if df.empty:
            keyboard = get_main_menu()
            await update.message.reply_text(format_error(f"Tidak data ditemukan untuk {symbol}"), parse_mode="HTML", reply_markup=keyboard)
            return

        price_prediction = prediction_indicator.predict_price(df)
        volume_analysis = volume_analyzer.analyze(df)

        price_text = format_price_prediction(symbol, price_prediction)
        keyboard = format_predict_result_menu()
        await update.message.reply_text(price_text, parse_mode="HTML", reply_markup=keyboard)

        vol_text = format_volume_analysis(symbol, volume_analysis)
        await update.message.reply_text(vol_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        await update.message.reply_text(format_error(f"Error: {str(e)}"), parse_mode="HTML")


async def predictall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    watchlist = load_watchlist()

    if not watchlist:
        keyboard = get_main_menu()
        await update.message.reply_text(format_error("Watchlist kosong."), parse_mode="HTML", reply_markup=keyboard)
        return

    await update.message.reply_text(format_info(f"Memprediksi {len(watchlist)} saham..."), parse_mode="HTML")

    for symbol in watchlist:
        try:
            df = collector.get_stock_data(symbol, days=60, timeframe="15m")
            if not df.empty:
                price_prediction = prediction_indicator.predict_price(df)
                price_text = format_price_prediction(symbol, price_prediction)
                await update.message.reply_text(price_text, parse_mode="HTML")
        except Exception:
            pass

    keyboard = get_main_menu()
    await update.message.reply_text(format_info("Prediksi selesai!"), parse_mode="HTML", reply_markup=keyboard)


async def intraday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.intraday_scanner import IntradayScanner
    from formatter import format_intraday_signal, format_intraday_signals, get_intraday_menu, get_intraday_result_menu, format_info, format_error

    session = IntradayScanner(config).get_current_session()
    if session == "closed":
        keyboard = get_main_menu()
        await update.message.reply_text(
            format_info("Market sedang tutup. Intraday scan hanya tersedia saat market hours (09:00-16:00 WIB)."),
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    if not context.args:
        keyboard = get_intraday_menu()
        await update.message.reply_text(
            format_info("Pilih jenis scan intraday:"),
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    symbol = context.args[0].upper()
    await process_intraday_single(update, context, symbol)


async def process_intraday_single(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
    from src.intraday_scanner import IntradayScanner
    from formatter import format_intraday_signal, get_intraday_result_menu, format_info, format_error

    await update.message.reply_text(format_info(f"Analisis intraday {symbol} dengan GLM AI..."), parse_mode="HTML")

    try:
        scanner = IntradayScanner(config)
        result = scanner.scan_stock(symbol)

        if result:
            text = format_intraday_signal(result)
            keyboard = get_intraday_result_menu()
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            keyboard = get_intraday_result_menu()
            await update.message.reply_text(
                format_info(f"Tidak ada sinyal intraday untuk {symbol}"),
                parse_mode="HTML",
                reply_markup=keyboard
            )
    except Exception as e:
        await update.message.reply_text(format_error(f"Error: {str(e)}"), parse_mode="HTML")


async def intraday_scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.intraday_scanner import IntradayScanner
    from formatter import format_intraday_signals, get_intraday_result_menu, format_info, format_error

    session = IntradayScanner(config).get_current_session()
    if session == "closed":
        keyboard = get_main_menu()
        await update.message.reply_text(
            format_info("Market sedang tutup."),
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    await update.message.reply_text(format_info("Scan intraday semua watchlist dengan GLM AI..."), parse_mode="HTML")

    try:
        scanner = IntradayScanner(config)
        signals = scanner.scan_for_group()

        if signals:
            text = format_intraday_signals(signals)
            keyboard = get_intraday_result_menu()
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)

            for signal in signals[:5]:
                from formatter import format_intraday_signal
                text = format_intraday_signal(signal)
                await update.message.reply_text(text, parse_mode="HTML")
        else:
            keyboard = get_intraday_result_menu()
            await update.message.reply_text(
                format_info("Tidak ada sinyal intraday ditemukan"),
                parse_mode="HTML",
                reply_markup=keyboard
            )
    except Exception as e:
        await update.message.reply_text(format_error(f"Error: {str(e)}"), parse_mode="HTML")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "screen":
        await query.edit_message_text("Ketik kode saham (contoh: BBCA TLKM BBRI):")
        context.user_data["state"] = "waiting_screen"

    elif data == "watchlist":
        watchlist = load_watchlist()
        text = format_watchlist(watchlist)
        keyboard = get_main_menu()
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data == "status":
        status = collector.get_market_status()
        text = format_market_status(status)
        keyboard = get_main_menu()
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data == "analyze":
        await query.edit_message_text("Ketik kode saham untuk dianalisis:")
        context.user_data["state"] = "waiting_analyze"

    elif data == "risk":
        risk = position_sizer.get_risk_summary()
        text = format_risk_info(risk)
        keyboard = get_main_menu()
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data == "alert":
        user_id = str(update.effective_user.id)
        if user_id not in user_settings:
            user_settings[user_id] = {"alert_enabled": True, "interval": 15}
        is_on = user_settings[user_id]["alert_enabled"]
        status = "ON" if is_on else "OFF"
        text = f"<b>Auto Alert:</b> {status}"
        keyboard = get_alert_menu(is_on)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data == "alert_on":
        await alert_on_command(update, context)

    elif data == "alert_off":
        await alert_off_command(update, context)

    elif data == "settings":
        user_id = str(update.effective_user.id)
        if user_id not in user_settings:
            user_settings[user_id] = {"alert_enabled": True, "interval": 15}
        settings = user_settings[user_id]
        text = f"""
<b>Settings</b>

<b>Auto Alert:</b> {'ON' if settings['alert_enabled'] else 'OFF'}
<b>Interval:</b> {settings['interval']} menit
"""
        keyboard = get_main_menu()
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data == "help":
        text = format_help()
        keyboard = get_back_menu()
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data == "main_menu":
        text = format_welcome()
        keyboard = get_main_menu()
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)

    elif data == "screen_again":
        await query.edit_message_text("Ketik kode saham (contoh: BBCA TLKM BBRI):")
        context.user_data["state"] = "waiting_screen"

    elif data == "predict":
        keyboard = format_prediction_menu()
        await query.edit_message_text("Pilih jenis prediksi:", reply_markup=keyboard)

    elif data == "predict_single":
        await query.edit_message_text("Ketik kode saham untuk prediksi:")
        context.user_data["state"] = "waiting_predict"

    elif data == "predict_all":
        await query.edit_message_text("Memprediksi semua watchlist...")
        watchlist = load_watchlist()
        for symbol in watchlist:
            try:
                df = collector.get_stock_data(symbol, days=60, timeframe="15m")
                if not df.empty:
                    price_prediction = prediction_indicator.predict_price(df)
                    price_text = format_price_prediction(symbol, price_prediction)
                    await query.message.reply_text(price_text, parse_mode="HTML")
            except Exception:
                pass
        keyboard = get_main_menu()
        await query.message.reply_text("Prediksi selesai!", reply_markup=keyboard)

    elif data == "upload":
        await query.edit_message_text("Uploading to GitHub...")
        await process_upload(update, context)

    elif data == "intraday_scan":
        from src.intraday_scanner import IntradayScanner
        from formatter import format_intraday_signal, get_intraday_result_menu

        session = IntradayScanner(config).get_current_session()
        if session == "closed":
            keyboard = get_main_menu()
            await query.edit_message_text("Market sedang tutup.", reply_markup=keyboard)
            return

        await query.edit_message_text("Scan intraday dengan GLM AI...")
        try:
            scanner = IntradayScanner(config)
            signals = scanner.scan_for_group()

            if signals:
                for signal in signals[:5]:
                    from formatter import format_intraday_signal
                    text = format_intraday_signal(signal)
                    await query.message.reply_text(text, parse_mode="HTML")
            else:
                await query.message.reply_text("Tidak ada sinyal intraday")

            keyboard = get_intraday_result_menu()
            await query.message.reply_text("Scan selesai!", reply_markup=keyboard)
        except Exception as e:
            await query.message.reply_text(f"Error: {str(e)}")

    elif data == "intraday_scan_all":
        await intraday_scan_command(update, context)

    elif data == "intraday":
        from formatter import get_intraday_menu
        keyboard = get_intraday_menu()
        await query.edit_message_text("Pilih jenis scan intraday:", reply_markup=keyboard)


async def process_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        project_dir = Path(__file__).parent.parent

        git_paths = [
            r"C:\Users\sony.helmi\AppData\Local\Programs\Git\cmd\git.exe",
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
            r"C:\Program Files\GitHub\bin\git.exe",
        ]
        git_cmd = "git"
        for path in git_paths:
            if Path(path).exists():
                git_cmd = path
                break

        result = subprocess.run(
            [git_cmd, "add", "."],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            if update.callback_query:
                await update.callback_query.message.reply_text(format_error(f"Git add failed: {result.stderr}"), parse_mode="HTML")
            return

        result = subprocess.run(
            [git_cmd, "status", "--porcelain"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        if not result.stdout.strip():
            keyboard = get_main_menu()
            if update.callback_query:
                await update.callback_query.message.reply_text(format_info("Tidak ada perubahan untuk di-upload"), parse_mode="HTML", reply_markup=keyboard)
            return

        commit_msg = f"Auto update from Telegram Bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        result = subprocess.run(
            [git_cmd, "commit", "-m", commit_msg],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            if update.callback_query:
                await update.callback_query.message.reply_text(format_error(f"Git commit failed: {result.stderr}"), parse_mode="HTML")
            return

        result = subprocess.run(
            [git_cmd, "push", "origin", "main"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            if update.callback_query:
                await update.callback_query.message.reply_text(format_error(f"Git push failed: {result.stderr}"), parse_mode="HTML")
            return

        text = f"""
<b>Upload Berhasil!</b>

<b>Commit:</b> {commit_msg}
<b>Branch:</b> main
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>Repository:</b>
https://github.com/javartmedia/idx-screener
"""
        keyboard = get_main_menu()
        if update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)

    except subprocess.TimeoutExpired:
        if update.callback_query:
            await update.callback_query.message.reply_text(format_error("Git command timeout"), parse_mode="HTML")
    except FileNotFoundError:
        if update.callback_query:
            await update.callback_query.message.reply_text(
                format_error("Git tidak terinstall. Install dari: https://git-scm.com/download/win"),
                parse_mode="HTML"
            )
    except Exception as e:
        if update.callback_query:
            await update.callback_query.message.reply_text(format_error(f"Error: {str(e)}"), parse_mode="HTML")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")

    if state == "waiting_screen":
        context.user_data["state"] = None
        symbols = update.message.text.upper().split()
        await process_screen(update, context, symbols)

    elif state == "waiting_analyze":
        context.user_data["state"] = None
        symbol = update.message.text.upper().strip()
        await process_analyze(update, context, symbol)

    elif state == "waiting_add":
        context.user_data["state"] = None
        symbol = update.message.text.upper().strip()
        watchlist = load_watchlist()
        if symbol in watchlist:
            keyboard = get_main_menu()
            await update.message.reply_text(format_info(f"{symbol} sudah ada di watchlist"), parse_mode="HTML", reply_markup=keyboard)
        else:
            watchlist.append(symbol)
            save_watchlist(watchlist)
            keyboard = get_main_menu()
            await update.message.reply_text(format_success(f"{symbol} ditambahkan ke watchlist"), parse_mode="HTML", reply_markup=keyboard)

    elif state == "waiting_predict":
        context.user_data["state"] = None
        symbol = update.message.text.upper().strip()
        await process_predict(update, context, symbol)

    elif state == "waiting_remove":
        context.user_data["state"] = None
        symbol = update.message.text.upper().strip()
        watchlist = load_watchlist()
        if symbol not in watchlist:
            keyboard = get_main_menu()
            await update.message.reply_text(format_info(f"{symbol} tidak ada di watchlist"), parse_mode="HTML", reply_markup=keyboard)
        else:
            watchlist.remove(symbol)
            save_watchlist(watchlist)
            keyboard = get_main_menu()
            await update.message.reply_text(format_success(f"{symbol} dihapus dari watchlist"), parse_mode="HTML", reply_markup=keyboard)

    elif state is None:
        text = update.message.text.lower()

        if text.startswith("/screen"):
            await screen_command(update, context)
        elif text.startswith("/analyze"):
            await analyze_command(update, context)
        elif text.startswith("/predict"):
            await predict_command(update, context)
        elif text.startswith("/predictall"):
            await predictall_command(update, context)
        elif text.startswith("/add"):
            await add_command(update, context)
        elif text.startswith("/remove"):
            await remove_command(update, context)
        elif text.startswith("/s "):
            args = text.replace("/s ", "").split()
            context.args = args
            await screen_command(update, context)
        elif text.startswith("/a "):
            args = text.replace("/a ", "").split()
            context.args = args
            await analyze_command(update, context)
        elif text.startswith("/p "):
            args = text.replace("/p ", "").split()
            context.args = args
            await predict_command(update, context)
        elif text.startswith("/upload"):
            await upload_command(update, context)
        elif text.startswith("/deploy"):
            await upload_command(update, context)


async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_info("Uploading to GitHub..."), parse_mode="HTML")

    try:
        project_dir = Path(__file__).parent.parent

        result = subprocess.run(
            ["git", "add", "."],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            await update.message.reply_text(format_error(f"Git add failed: {result.stderr}"), parse_mode="HTML")
            return

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        if not result.stdout.strip():
            keyboard = get_main_menu()
            await update.message.reply_text(format_info("Tidak ada perubahan untuk di-upload"), parse_mode="HTML", reply_markup=keyboard)
            return

        commit_msg = f"Auto update from Telegram Bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if context.args:
            commit_msg = " ".join(context.args)

        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            await update.message.reply_text(format_error(f"Git commit failed: {result.stderr}"), parse_mode="HTML")
            return

        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            await update.message.reply_text(format_error(f"Git push failed: {result.stderr}"), parse_mode="HTML")
            return

        text = f"""
<b>Upload Berhasil!</b>

<b>Commit:</b> {commit_msg}
<b>Branch:</b> main
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>Repository:</b>
https://github.com/javartmedia/idx-screener
"""
        keyboard = get_main_menu()
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)

    except subprocess.TimeoutExpired:
        await update.message.reply_text(format_error("Git command timeout"), parse_mode="HTML")
    except FileNotFoundError:
        await update.message.reply_text(format_error("Git tidak terinstall"), parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(format_error(f"Error: {str(e)}"), parse_mode="HTML")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Exception: {context.error}")
