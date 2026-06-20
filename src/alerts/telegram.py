import requests
from typing import Optional
from datetime import datetime

from ..config import AppConfig
from ..data_models import Signal


class TelegramAlert:
    def __init__(self, config: AppConfig):
        self.enabled = config.alerts.telegram.enabled
        self.bot_token = config.alerts.telegram.bot_token
        self.chat_id = config.alerts.telegram.chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message: str) -> bool:
        if not self.enabled:
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
            }

            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    def send_signal(self, signal: Signal) -> bool:
        message = self._format_signal(signal)
        return self.send_message(message)

    def send_signals(self, signals: list) -> bool:
        if not signals:
            return True

        message = self._format_signals(signals)
        return self.send_message(message)

    def send_summary(self, signals: list, date: datetime = None) -> bool:
        if date is None:
            date = datetime.now()

        message = self._format_summary(signals, date)
        return self.send_message(message)

    def _format_signal(self, signal: Signal) -> str:
        indicators = signal.indicators

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

        macd_icon = "✅" if indicators.get("macd_bullish", False) else "⚠️"
        trend = indicators.get("trend", "unknown")
        trend_icon = "✅" if "uptrend" in trend.lower() else "⚠️"

        message = f"""
🔔 <b>{signal.signal_type} SIGNAL - {signal.symbol}</b>

💰 <b>Entry:</b> Rp {signal.entry_price:,.0f}
🛑 <b>Stop Loss:</b> Rp {signal.stop_loss:,.0f}
🎯 <b>Take Profit:</b> Rp {signal.take_profit:,.0f}
📊 <b>Score:</b> {signal.score}/100

<b>Indikator:</b>
{volume_icon} Volume: {volume_ratio:.1f}x average
{rsi_icon} RSI: {rsi:.0f} ({rsi_status})
{macd_icon} MACD: {'Bullish' if indicators.get('macd_bullish', False) else 'Bearish'}
{trend_icon} Trend: {trend}

⏰ {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
        return message.strip()

    def _format_signals(self, signals: list) -> str:
        header = f"📊 <b>Found {len(signals)} signal(s)</b>\n\n"

        signal_messages = []
        for signal in signals[:5]:
            signal_messages.append(
                f"• <b>{signal.symbol}</b> - Score: {signal.score}, "
                f"Entry: Rp {signal.entry_price:,.0f}"
            )

        return header + "\n".join(signal_messages)

    def _format_summary(self, signals: list, date: datetime) -> str:
        total = len(signals)
        strong = len([s for s in signals if s.score >= 80])
        medium = len([s for s in signals if 60 <= s.score < 80])

        message = f"""
📊 <b>DAILY SUMMARY - {date.strftime('%Y-%m-%d')}</b>

📈 <b>Total Signals:</b> {total}
✅ <b>Strong Signals:</b> {strong}
⚠️ <b>Medium Signals:</b> {medium}
"""

        if signals:
            message += "\n<b>Top Signals:</b>\n"
            for signal in signals[:5]:
                message += f"• <b>{signal.symbol}</b> - Score: {signal.score}\n"

        return message.strip()
