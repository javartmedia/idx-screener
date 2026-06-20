import schedule
import time
from datetime import datetime, timedelta
from typing import Callable, Optional
import threading

from ..config import AppConfig, load_config, load_watchlist
from ..collector import StockBitCollector
from ..screener import MultiIndicatorScreener
from ..alerts import CLIAlert, TelegramAlert, EmailAlert


class AutoScheduler:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.collector = StockBitCollector()
        self.screener = MultiIndicatorScreener(self.config)
        self.cli_alert = CLIAlert()
        self.telegram_alert = TelegramAlert(self.config)
        self.email_alert = EmailAlert(self.config)
        self.watchlist = load_watchlist()
        self.running = False
        self.last_signals = []

    def start(self):
        self.running = True
        self.cli_alert.show_success("Auto scheduler started")

        interval = self.config.scheduler.interval_minutes
        schedule.every(interval).minutes.do(self._run_screening)

        schedule.every().day.at("08:55").do(self._market_pre_open)
        schedule.every().day.at("09:00").do(self._market_open)
        schedule.every().day.at("15:45").do(self._last_screening)
        schedule.every().day.at("16:00").do(self._market_close)
        schedule.every().day.at(self.config.alerts.summary_time).do(self._send_daily_summary)

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
