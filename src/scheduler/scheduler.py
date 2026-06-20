import schedule
import time
from datetime import datetime, timedelta
from typing import Callable, Optional
import threading

from ..config import AppConfig, load_config, load_watchlist
from ..collector import StockBitCollector
from ..screener import MultiIndicatorScreener
from ..alerts import CLIAlert, TelegramAlert, EmailAlert
from ..intraday_scanner import IntradayScanner


class AutoScheduler:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.collector = StockBitCollector()
        self.screener = MultiIndicatorScreener(self.config)
        self.cli_alert = CLIAlert()
        self.telegram_alert = TelegramAlert(self.config)
        self.email_alert = EmailAlert(self.config)
        self.intraday_scanner = IntradayScanner(self.config)
        self.watchlist = load_watchlist()
        self.running = False
        self.last_signals = []
        self.last_intraday_signals = []

    def start(self):
        self.running = True
        self.cli_alert.show_success("Auto scheduler started")

        interval = self.config.scheduler.interval_minutes
        schedule.every(interval).minutes.do(self._run_screening)

        if self.config.intraday.enabled:
            intraday_interval = self.config.intraday.interval_minutes
            schedule.every(intraday_interval).minutes.do(self._run_intraday_scan)

        schedule.every().day.at("08:55").do(self._market_pre_open)
        schedule.every().day.at("09:00").do(self._market_open)
        schedule.every().day.at("15:45").do(self._last_screening)
        schedule.every().day.at("16:00").do(self._market_close)
        schedule.every().day.at(self.config.alerts.summary_time).do(self._send_daily_summary)

        if self.config.intraday.enabled and self.config.intraday.send_summary:
            schedule.every().day.at(self.config.intraday.summary_time).do(self._send_intraday_summary)

        self._run_screening()

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        self.running = False
        schedule.clear()
        self.cli_alert.show_success("Auto scheduler stopped")

    def _is_market_hours(self) -> bool:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        return self.config.scheduler.trading_hours_start <= current_time <= self.config.scheduler.trading_hours_end

    def _is_intraday_hours(self) -> bool:
        if not self.config.intraday.enabled:
            return False
        now = datetime.now()
        current = now.hour * 60 + now.minute

        morning_start = self._time_to_minutes(self.config.intraday.morning_start)
        morning_end = self._time_to_minutes(self.config.intraday.morning_end)
        afternoon_start = self._time_to_minutes(self.config.intraday.afternoon_start)
        afternoon_end = self._time_to_minutes(self.config.intraday.afternoon_end)

        return (morning_start <= current < morning_end) or (afternoon_start <= current < afternoon_end)

    def _time_to_minutes(self, time_str: str) -> int:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    def _market_pre_open(self):
        self.cli_alert.show_info("Market opening in 5 minutes...")

    def _market_open(self):
        self.cli_alert.show_success("Market is now OPEN")

    def _last_screening(self):
        self.cli_alert.show_info("Last screening before market close...")
        self._run_screening()

    def _market_close(self):
        self.cli_alert.show_info("Market is now CLOSED")

    def _send_daily_summary(self):
        self.cli_alert.show_summary(self.last_signals)
        self.telegram_alert.send_summary(self.last_signals)
        self.email_alert.send_summary(self.last_signals)
        self.last_signals = []

    def _send_intraday_summary(self):
        if not self.last_intraday_signals:
            return

        self.cli_alert.show_info("Sending intraday summary...")
        group_chat_id = self.config.intraday.group_chat_id

        if self.config.intraday.enabled and self.telegram_alert.enabled:
            from ..glm_analyzer import GLMAnalyzer
            glm = GLMAnalyzer(self.config)
            summary = glm.generate_market_summary(
                self.last_intraday_signals,
                {}
            )
            self.telegram_alert.send_intraday_summary(
                self.last_intraday_signals,
                summary,
                group_chat_id
            )

        self.last_intraday_signals = []

    def _run_screening(self):
        if not self._is_market_hours():
            return

        self.cli_alert.show_info("Running screening...")

        stocks_data = {}
        for symbol in self.watchlist:
            try:
                df = self.collector.get_stock_data(symbol, days=60, timeframe="15m")
                if not df.empty:
                    stocks_data[symbol] = df
            except Exception as e:
                self.cli_alert.show_error(f"Error fetching {symbol}: {e}")

        signals = self.screener.screen_multiple(stocks_data)

        if signals:
            self.last_signals.extend(signals)
            self.cli_alert.show_signals(signals)

            for signal in signals:
                self.telegram_alert.send_signal(signal)

    def _run_intraday_scan(self):
        if not self._is_intraday_hours():
            return

        self.cli_alert.show_info("Running intraday scan with GLM...")

        try:
            signals = self.intraday_scanner.scan_for_group()

            if signals:
                self.last_intraday_signals.extend(signals)

                for signal in signals:
                    if signal.get("confidence", 0) >= self.config.intraday.min_confidence:
                        group_chat_id = self.config.intraday.group_chat_id
                        self.telegram_alert.send_intraday_signal(signal, group_chat_id)
                        self.cli_alert.show_info(f"Sent {signal.get('action')} signal for {signal.get('symbol')}")

        except Exception as e:
            self.cli_alert.show_error(f"Intraday scan error: {e}")

    def run_once(self):
        self.cli_alert.show_info("Running one-time screening...")

        stocks_data = {}
        for symbol in self.watchlist:
            try:
                df = self.collector.get_stock_data(symbol, days=60, timeframe="15m")
                if not df.empty:
                    stocks_data[symbol] = df
            except Exception as e:
                self.cli_alert.show_error(f"Error fetching {symbol}: {e}")

        signals = self.screener.screen_multiple(stocks_data)
        self.cli_alert.show_signals(signals)
        return signals

    def run_intraday_once(self):
        self.cli_alert.show_info("Running one-time intraday scan...")

        try:
            signals = self.intraday_scanner.scan_for_group()

            if signals:
                self.last_intraday_signals.extend(signals)

                for signal in signals:
                    if signal.get("confidence", 0) >= self.config.intraday.min_confidence:
                        group_chat_id = self.config.intraday.group_chat_id
                        self.telegram_alert.send_intraday_signal(signal, group_chat_id)
                        self.cli_alert.show_info(f"Sent {signal.get('action')} signal for {signal.get('symbol')}")

            return signals

        except Exception as e:
            self.cli_alert.show_error(f"Intraday scan error: {e}")
            return []
