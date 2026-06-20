import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List

from ..config import AppConfig
from ..data_models import Signal


class EmailAlert:
    def __init__(self, config: AppConfig):
        self.enabled = config.alerts.email.enabled
        self.smtp_server = config.alerts.email.smtp_server
        self.smtp_port = config.alerts.email.smtp_port
        self.sender = config.alerts.email.sender
        self.password = config.alerts.email.password
        self.receiver = config.alerts.email.receiver

    def send_email(self, subject: str, body: str) -> bool:
        if not self.enabled:
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = self.receiver
            msg["Subject"] = subject

            html_body = self._convert_to_html(body)
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Email error: {e}")
            return False

    def send_signal(self, signal: Signal) -> bool:
        subject = f"🔔 {signal.signal_type} Signal - {signal.symbol}"
        body = self._format_signal(signal)
        return self.send_email(subject, body)

    def send_signals(self, signals: List[Signal]) -> bool:
        if not signals:
            return True

        subject = f"📊 IDX Screener - {len(signals)} Signal(s) Found"
        body = self._format_signals(signals)
        return self.send_email(subject, body)

    def send_summary(self, signals: List[Signal], date: datetime = None) -> bool:
        if date is None:
            date = datetime.now()

        subject = f"📊 Daily Summary - {date.strftime('%Y-%m-%d')}"
        body = self._format_summary(signals, date)
        return self.send_email(subject, body)

    def _format_signal(self, signal: Signal) -> str:
        indicators = signal.indicators

        volume_ratio = indicators.get("volume_ratio", 0)
        rsi = indicators.get("rsi", 50)
        macd_bullish = indicators.get("macd_bullish", False)
        trend = indicators.get("trend", "unknown")

        return f"""
IDX Screener - {signal.signal_type} Signal

Symbol: {signal.symbol}
Entry Price: Rp {signal.entry_price:,.0f}
Stop Loss: Rp {signal.stop_loss:,.0f}
Take Profit: Rp {signal.take_profit:,.0f}
Score: {signal.score}/100

Indicators:
- Volume: {volume_ratio:.1f}x average
- RSI: {rsi:.0f}
- MACD: {'Bullish' if macd_bullish else 'Bearish'}
- Trend: {trend}

Timestamp: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

    def _format_signals(self, signals: List[Signal]) -> str:
        header = f"Found {len(signals)} signal(s)\n\n"

        signal_list = []
        for signal in signals:
            signal_list.append(
                f"• {signal.symbol} - Score: {signal.score}, "
                f"Entry: Rp {signal.entry_price:,.0f}"
            )

        return header + "\n".join(signal_list)

    def _format_summary(self, signals: List[Signal], date: datetime) -> str:
        total = len(signals)
        strong = len([s for s in signals if s.score >= 80])
        medium = len([s for s in signals if 60 <= s.score < 80])

        message = f"""
Daily Summary - {date.strftime('%Y-%m-%d')}

Total Signals: {total}
Strong Signals: {strong}
Medium Signals: {medium}
"""

        if signals:
            message += "\nTop Signals:\n"
            for signal in signals[:5]:
                message += f"• {signal.symbol} - Score: {signal.score}\n"

        return message

    def _convert_to_html(self, text: str) -> str:
        html = text.replace("\n", "<br>")
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .signal {{ background-color: #f0f0f0; padding: 10px; margin: 10px 0; }}
                .strong {{ color: green; }}
                .warning {{ color: orange; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        return html
