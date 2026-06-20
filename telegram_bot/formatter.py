from datetime import datetime
from typing import List


def format_signal(signal: dict) -> str:
    symbol = signal.get("symbol", "???")
    score = signal.get("score", 0)
    entry = signal.get("entry_price", 0)
    stop_loss = signal.get("stop_loss", 0)
    take_profit = signal.get("take_profit", 0)
    indicators = signal.get("indicators", {})

    if score >= 80:
        strength = "🟢 STRONG"
    elif score >= 60:
        strength = "🟡 MEDIUM"
    elif score >= 40:
        strength = "🟠 WEAK"
    else:
        strength = "🔴 NO SIGNAL"

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
<b>🔔 {signal.get('signal_type', 'BUY')} SIGNAL - {symbol}</b>

<b>💰 Entry:</b> Rp {entry:,.0f}
<b>🛑 Stop Loss:</b> Rp {stop_loss:,.0f}
<b>🎯 Take Profit:</b> Rp {take_profit:,.0f}
<b>📊 Score:</b> {score}/100 ({strength})

<b>Indikator:</b>
{volume_icon} Volume: {volume_ratio:.1f}x average
{rsi_icon} RSI: {rsi:.0f} ({rsi_status})
{macd_icon} MACD: {'Bullish' if macd_bullish else 'Bearish'}
{trend_icon} Trend: {trend}

<i>⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
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
<b>📊 Analysis for {symbol}</b>

<b>💰 Harga:</b> Rp {last_price:,.0f}
<b>{change_icon} Change:</b> {change:+.2f}%

<b>Indikator:</b>
• Volume Ratio: {indicators.get('volume_ratio', 0):.1f}x
• RSI: {indicators.get('rsi', 0):.0f}
• MACD: {'Bullish' if indicators.get('bullish', False) else 'Bearish'}
• Trend: {indicators.get('trend', 'unknown')}
• Bollinger: {indicators.get('position', 'unknown')}

<b>Signal:</b>
• Score: {signal.get('total_score', 0)}/100
• Strength: {signal.get('strength', 'N/A')}
• Valid: {'Yes' if signal.get('is_valid', False) else 'No'}
"""
    return text.strip()


def format_signals(signals: List[dict]) -> str:
    if not signals:
        return "❌ <b>No signals found</b>"

    text = f"📊 <b>Found {len(signals)} signal(s)</b>\n\n"

    for i, signal in enumerate(signals[:10], 1):
        symbol = signal.get("symbol", "???")
        score = signal.get("score", 0)
        entry = signal.get("entry_price", 0)

        if score >= 80:
            icon = "🟢"
        elif score >= 60:
            icon = "🟡"
        else:
            icon = "🟠"

        text += f"{i}. {icon} <b>{symbol}</b> - Score: {score}, Entry: Rp {entry:,.0f}\n"

    return text.strip()


def format_watchlist(watchlist: List[str]) -> str:
    if not watchlist:
        return "📋 <b>Watchlist kosong</b>"

    text = f"📋 <b>Watchlist ({len(watchlist)} stocks)</b>\n\n"

    for i, symbol in enumerate(watchlist, 1):
        text += f"{i}. <b>{symbol}</b>\n"

    return text.strip()


def format_market_status(status: dict) -> str:
    market_status = status.get("status", "UNKNOWN")
    current_time = status.get("current_time", "???:???")

    if market_status == "OPEN":
        icon = "🟢"
    elif market_status in ["PRE_MARKET", "POST_MARKET"]:
        icon = "🟡"
    else:
        icon = "🔴"

    text = f"""
<b>📈 Market Status</b>

<b>Status:</b> {icon} {market_status}
<b>Current Time:</b> {current_time}
<b>Market Open:</b> 09:00 WIB
<b>Market Close:</b> 16:00 WIB
"""
    return text.strip()


def format_risk_info(risk: dict) -> str:
    text = f"""
<b>🛡️ Risk Management</b>

<b>💰 Capital:</b> Rp {risk.get('capital', 0):,.0f}
<b>📊 Risk per Trade:</b> {risk.get('risk_per_trade', 0) * 100}%
<b>⚠️ Max Risk Amount:</b> Rp {risk.get('max_risk_amount', 0):,.0f}
<b>📈 Max Positions:</b> {risk.get('max_positions', 0)}
<b>📉 Max Daily Loss:</b> {risk.get('max_daily_loss', 0) * 100}%
<b>💸 Max Daily Loss Amount:</b> Rp {risk.get('max_daily_loss_amount', 0):,.0f}
"""
    return text.strip()


def format_welcome() -> str:
    text = """
<b>🤖 IDX Screener Bot</b>

<b>Selamat datang!</b>

Bot ini membantu Anda screening saham Indonesia (IDX) untuk strategi Beli Pagi, Jual Sore.

<b>Command yang tersedia:</b>
/help - Lihat semua command
/screen &lt;saham&gt; - Screen saham
/screenall - Screen semua watchlist
/analyze &lt;saham&gt; - Analisis detail
/watchlist - Lihat daftar saham
/add &lt;saham&gt; - Tambah ke watchlist
/remove &lt;saham&gt; - Hapus dari watchlist
/status - Cek market status
/risk - Info risk management
/alert on/off - Toggle auto alert
/interval &lt;menit&gt; - Set interval alert

<i>Gunakan /help untuk melihat semua command.</i>
"""
    return text.strip()


def format_help() -> str:
    text = """
<b>📖 Help - IDX Screener Bot</b>

<b>Command List:</b>

<b>📊 Screening:</b>
/screen &lt;saham&gt; - Screen 1 saham
/screen BBCA TLKM - Screen multi saham
/screenall - Screen semua watchlist
/analyze &lt;saham&gt; - Analisis detail

<b>📋 Watchlist:</b>
/watchlist - Lihat daftar saham
/add &lt;saham&gt; - Tambah ke watchlist
/remove &lt;saham&gt; - Hapus dari watchlist

<b>⚙️ Info:</b>
/status - Cek market status
/risk - Info risk management

<b>🔔 Alert:</b>
/alert on - Aktifkan auto alert
/alert off - Matikan auto alert
/interval &lt;menit&gt; - Set interval (1-60)

<b>📖 Lainnya:</b>
/start - Welcome message
/help - Tampilkan help ini

<i>Contoh: /screen BBCA</i>
"""
    return text.strip()


def format_error(message: str) -> str:
    return f"❌ <b>Error:</b> {message}"


def format_success(message: str) -> str:
    return f"✅ <b>{message}</b>"


def format_info(message: str) -> str:
    return f"ℹ️ <b>{message}</b>"


def format_daily_summary(signals: List[dict], date: datetime = None) -> str:
    if date is None:
        date = datetime.now()

    total = len(signals)
    strong = len([s for s in signals if s.get("score", 0) >= 80])
    medium = len([s for s in signals if 60 <= s.get("score", 0) < 80])

    text = f"""
<b>📊 Daily Summary - {date.strftime('%Y-%m-%d')}</b>

<b>📈 Total Signals:</b> {total}
<b>🟢 Strong Signals:</b> {strong}
<b>🟡 Medium Signals:</b> {medium}
"""

    if signals:
        text += "\n<b>Top Signals:</b>\n"
        for signal in signals[:5]:
            symbol = signal.get("symbol", "???")
            score = signal.get("score", 0)
            text += f"• <b>{symbol}</b> - Score: {score}\n"

    return text.strip()
