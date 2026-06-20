from datetime import datetime
from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("PREDIKSI NEXT DAY", callback_data="predict")],
        [InlineKeyboardButton("SCREEN SAHAM", callback_data="screen")],
        [
            InlineKeyboardButton("Watchlist", callback_data="watchlist"),
            InlineKeyboardButton("Status", callback_data="status"),
        ],
        [
            InlineKeyboardButton("Analisis", callback_data="analyze"),
            InlineKeyboardButton("Risk Info", callback_data="risk"),
        ],
        [
            InlineKeyboardButton("Alert ON/OFF", callback_data="alert"),
            InlineKeyboardButton("Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("UPLOAD GITHUB", callback_data="upload"),
            InlineKeyboardButton("HELP", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_screen_result_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📊 Screen Lagi", callback_data="screen"),
            InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_alert_menu(is_on: bool) -> InlineKeyboardMarkup:
    if is_on:
        alert_text = "🔴 Matikan Alert"
        alert_data = "alert_off"
    else:
        alert_text = "🟢 Aktifkan Alert"
        alert_data = "alert_on"

    keyboard = [
        [InlineKeyboardButton(alert_text, callback_data=alert_data)],
        [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def format_signal(signal: dict) -> str:
    symbol = signal.get("symbol", "???")
    score = signal.get("score", 0)
    entry = signal.get("entry_price", 0)
    stop_loss = signal.get("stop_loss", 0)
    take_profit = signal.get("take_profit", 0)
    indicators = signal.get("indicators", {})

    if score >= 80:
        strength = "STRONG"
    elif score >= 60:
        strength = "MEDIUM"
    elif score >= 40:
        strength = "WEAK"
    else:
        strength = "NO SIGNAL"

    volume_ratio = indicators.get("volume_ratio", 0)
    volume_icon = "✅" if volume_ratio >= 2.0 else "⚠️"

    rsi = indicators.get("rsi", 50)
    if 30 < rsi < 70:
        rsi_icon = "✅"
        rsi_status = "Neutral"
    elif rsi <= 30:
        rsi_icon = "✅"
        rsi_status = "Oversold"
    else:
        rsi_icon = "⚠️"
        rsi_status = "Overbought"

    macd_bullish = indicators.get("macd_bullish", False)
    macd_icon = "✅" if macd_bullish else "⚠️"

    trend = indicators.get("trend", "unknown")
    trend_icon = "✅" if "uptrend" in trend.lower() else "⚠️"

    text = f"""
<b>BUY SIGNAL - {symbol}</b>

<b>Entry:</b> Rp {entry:,.0f}
<b>Stop Loss:</b> Rp {stop_loss:,.0f}
<b>Take Profit:</b> Rp {take_profit:,.0f}
<b>Score:</b> {score}/100 ({strength})

<b>Indikator:</b>
{volume_icon} Volume: {volume_ratio:.1f}x average
{rsi_icon} RSI: {rsi:.0f} ({rsi_status})
{macd_icon} MACD: {'Bullish' if macd_bullish else 'Bearish'}
{trend_icon} Trend: {trend}

<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
    return text.strip()


def format_analysis(analysis: dict) -> str:
    symbol = analysis.get("symbol", "???")
    last_price = analysis.get("last_price", 0)
    change = analysis.get("change_percent", 0)
    indicators = analysis.get("indicators", {})
    signal = analysis.get("signal", {})

    change_icon = "📈" if change >= 0 else "📉"

    text = f"""
<b>Analysis for {symbol}</b>

<b>Harga:</b> Rp {last_price:,.0f}
<b>{change_icon} Change:</b> {change:+.2f}%

<b>Indikator:</b>
- Volume Ratio: {indicators.get('volume_ratio', 0):.1f}x
- RSI: {indicators.get('rsi', 0):.0f}
- MACD: {'Bullish' if indicators.get('bullish', False) else 'Bearish'}
- Trend: {indicators.get('trend', 'unknown')}
- Bollinger: {indicators.get('position', 'unknown')}

<b>Signal:</b>
- Score: {signal.get('total_score', 0)}/100
- Strength: {signal.get('strength', 'N/A')}
- Valid: {'Yes' if signal.get('is_valid', False) else 'No'}
"""
    return text.strip()


def format_signals(signals: List[dict]) -> str:
    if not signals:
        return "<b>No signals found</b>"

    text = f"<b>Found {len(signals)} signal(s)</b>\n\n"

    for i, signal in enumerate(signals[:10], 1):
        symbol = signal.get("symbol", "???")
        score = signal.get("score", 0)
        entry = signal.get("entry_price", 0)

        if score >= 80:
            icon = "[STRONG]"
        elif score >= 60:
            icon = "[MEDIUM]"
        else:
            icon = "[WEAK]"

        text += f"{i}. {icon} <b>{symbol}</b> - Score: {score}, Entry: Rp {entry:,.0f}\n"

    return text.strip()


def format_watchlist(watchlist: List[str]) -> str:
    if not watchlist:
        return "<b>Watchlist kosong</b>"

    text = f"<b>Watchlist ({len(watchlist)} stocks)</b>\n\n"

    for i, symbol in enumerate(watchlist, 1):
        text += f"{i}. <b>{symbol}</b>\n"

    return text.strip()


def format_market_status(status: dict) -> str:
    market_status = status.get("status", "UNKNOWN")
    current_time = status.get("current_time", "???:???")

    if market_status == "OPEN":
        icon = "OPEN"
    elif market_status in ["PRE_MARKET", "POST_MARKET"]:
        icon = "PREPARING"
    else:
        icon = "CLOSED"

    text = f"""
<b>Market Status</b>

<b>Status:</b> {icon}
<b>Current Time:</b> {current_time}
<b>Market Open:</b> 09:00 WIB
<b>Market Close:</b> 16:00 WIB
"""
    return text.strip()


def format_risk_info(risk: dict) -> str:
    text = f"""
<b>Risk Management</b>

<b>Capital:</b> Rp {risk.get('capital', 0):,.0f}
<b>Risk per Trade:</b> {risk.get('risk_per_trade', 0) * 100}%
<b>Max Risk Amount:</b> Rp {risk.get('max_risk_amount', 0):,.0f}
<b>Max Positions:</b> {risk.get('max_positions', 0)}
<b>Max Daily Loss:</b> {risk.get('max_daily_loss', 0) * 100}%
<b>Max Daily Loss Amount:</b> Rp {risk.get('max_daily_loss_amount', 0):,.0f}
"""
    return text.strip()


def format_welcome() -> str:
    text = """
<b>IDX Screener Bot</b>

<b>Selamat datang!</b>

Bot ini membantu Anda screening saham Indonesia (IDX) untuk strategi Beli Pagi, Jual Sore.

<b>Gunakan tombol di bawah untuk navigasi:</b>
"""
    return text.strip()


def format_help() -> str:
    text = """
<b>Help - IDX Screener Bot</b>

<b>Command List:</b>

<b>Screening:</b>
/screen &lt;saham&gt; - Screen 1 saham
/screen BBCA TLKM - Screen multi saham
/screenall - Screen semua watchlist
/analyze &lt;saham&gt; - Analisis detail

<b>Prediksi:</b>
/predict &lt;saham&gt; - Prediksi next day
/predictall - Prediksi semua watchlist

<b>Watchlist:</b>
/watchlist - Lihat daftar saham
/add &lt;saham&gt; - Tambah ke watchlist
/remove &lt;saham&gt; - Hapus dari watchlist

<b>Info:</b>
/status - Cek market status
/risk - Info risk management

<b>Alert:</b>
/alert on - Aktifkan auto alert
/alert off - Matikan auto alert
/interval &lt;menit&gt; - Set interval (1-60)

<b>GitHub Upload:</b>
/upload - Upload perubahan ke GitHub
/deploy - Upload perubahan ke GitHub

<b>Lainnya:</b>
/start - Welcome message
/help - Tampilkan help ini

<i>Contoh: /screen BBCA</i>
"""
    return text.strip()


def format_error(message: str) -> str:
    return f"<b>Error:</b> {message}"


def format_success(message: str) -> str:
    return f"<b>{message}</b>"


def format_info(message: str) -> str:
    return f"<b>{message}</b>"


def format_daily_summary(signals: List[dict], date: datetime = None) -> str:
    if date is None:
        date = datetime.now()

    total = len(signals)
    strong = len([s for s in signals if s.get("score", 0) >= 80])
    medium = len([s for s in signals if 60 <= s.get("score", 0) < 80])

    text = f"""
<b>Daily Summary - {date.strftime('%Y-%m-%d')}</b>

<b>Total Signals:</b> {total}
<b>Strong Signals:</b> {strong}
<b>Medium Signals:</b> {medium}
"""

    if signals:
        text += "\n<b>Top Signals:</b>\n"
        for signal in signals[:5]:
            symbol = signal.get("symbol", "???")
            score = signal.get("score", 0)
            text += f"- <b>{symbol}</b> - Score: {score}\n"

    return text.strip()


def format_price_prediction(symbol: str, prediction: dict) -> str:
    current = prediction.get("current_price", 0)
    low = prediction.get("predicted_low", 0)
    mid = prediction.get("predicted_mid", 0)
    high = prediction.get("predicted_high", 0)
    confidence = prediction.get("confidence", 0)
    support_1 = prediction.get("support_1", 0)
    support_2 = prediction.get("support_2", 0)
    resistance_1 = prediction.get("resistance_1", 0)
    resistance_2 = prediction.get("resistance_2", 0)
    trend = prediction.get("trend", "Unknown")
    momentum = prediction.get("momentum", "Unknown")
    change_pct = prediction.get("expected_change_pct", 0)

    if confidence >= 70:
        conf_level = "HIGH"
    elif confidence >= 50:
        conf_level = "MEDIUM"
    else:
        conf_level = "LOW"

    text = f"""
<b>NEXT DAY PREDICTION - {symbol}</b>

<b>Current Price:</b> Rp {current:,.0f}

<b>Prediksi Harga:</b>
- Low: Rp {low:,.0f}
- Mid: Rp {mid:,.0f}
- High: Rp {high:,.0f}

<b>Expected Change:</b> {change_pct:+.2f}%
<b>Confidence:</b> {confidence:.0f}% ({conf_level})

<b>Key Levels:</b>
- Resistance 2: Rp {resistance_2:,.0f}
- Resistance 1: Rp {resistance_1:,.0f}
- Support 1: Rp {support_1:,.0f}
- Support 2: Rp {support_2:,.0f}

<b>Trend:</b> {trend}
<b>Momentum:</b> {momentum}

<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>
"""
    return text.strip()


def format_volume_analysis(symbol: str, analysis: dict) -> str:
    avg_vol = analysis.get("avg_volume", 0)
    max_vol = analysis.get("max_volume", 0)
    min_vol = analysis.get("min_volume", 0)
    max_day = analysis.get("max_volume_day", "N/A")
    min_day = analysis.get("min_volume_day", "N/A")
    trend = analysis.get("volume_trend", "Unknown")
    trend_strength = analysis.get("trend_strength", "Unknown")
    obv_trend = analysis.get("obv_trend", "Unknown")
    accumulation = analysis.get("accumulation_phase", "Unknown")
    acc_signal = analysis.get("accumulation_signal", "Unknown")
    predicted = analysis.get("predicted_volume", 0)
    condition = analysis.get("volume_condition", "Unknown")
    has_spike = analysis.get("has_spike", False)
    spike_ratio = analysis.get("spike_ratio", 1.0)

    spike_text = "YES" if has_spike else "No"

    text = f"""
<b>VOLUME ANALYSIS - {symbol}</b>

<b>Volume Stats (7 Hari):</b>
- Average: {avg_vol:,.0f}
- Highest: {max_vol:,.0f} ({max_day})
- Lowest: {min_vol:,.0f} ({min_day})

<b>Volume Trend:</b>
- Direction: {trend}
- Strength: {trend_strength}

<b>OBV Analysis:</b>
- OBV Trend: {obv_trend}

<b>Accumulation/Distribution:</b>
- Phase: {accumulation}
- Signal: {acc_signal}

<b>Volume Spike:</b>
- Detected: {spike_text}
- Ratio: {spike_ratio:.1f}x average

<b>Prediction:</b>
- Expected Volume: {predicted:,.0f}
- Condition: {condition}

<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>
"""
    return text.strip()


def format_prediction_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Prediksi 1 Saham", callback_data="predict_single")],
        [InlineKeyboardButton("Prediksi Semua Watchlist", callback_data="predict_all")],
        [InlineKeyboardButton("Menu Utama", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def format_predict_result_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Prediksi Lagi", callback_data="predict"),
            InlineKeyboardButton("Menu Utama", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
