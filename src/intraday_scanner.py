from datetime import datetime
from typing import Optional, List, Dict, Any
import pytz

from .config import AppConfig, load_config, load_watchlist
from .collector import StockBitCollector
from .indicators import VolumeIndicator, TrendIndicator, MomentumIndicator, VolatilityIndicator
from .glm_analyzer import GLMAnalyzer


class IntradayScanner:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.collector = StockBitCollector()
        self.glm = GLMAnalyzer(self.config)
        self.watchlist = load_watchlist()
        self.tz = pytz.timezone("Asia/Jakarta")

        self.volume_ind = VolumeIndicator(
            lookback_period=self.config.indicators.volume.lookback_period,
            spike_threshold=self.config.indicators.volume.spike_threshold,
        )
        self.trend_ind = TrendIndicator(
            ema_fast=self.config.indicators.trend.ema_fast,
            ema_slow=self.config.indicators.trend.ema_slow,
            adx_threshold=self.config.indicators.trend.adx_threshold,
        )
        self.momentum_ind = MomentumIndicator(
            rsi_period=self.config.indicators.momentum.rsi_period,
            rsi_oversold=self.config.indicators.momentum.rsi_oversold,
            rsi_overbought=self.config.indicators.momentum.rsi_overbought,
            macd_fast=self.config.indicators.momentum.macd_fast,
            macd_slow=self.config.indicators.momentum.macd_slow,
            macd_signal=self.config.indicators.momentum.macd_signal,
        )
        self.volatility_ind = VolatilityIndicator(
            bb_period=self.config.indicators.volatility.bb_period,
            bb_std=self.config.indicators.volatility.bb_std,
            atr_period=self.config.indicators.volatility.atr_period,
        )

    def get_current_session(self) -> str:
        now = datetime.now(self.tz)
        hour = now.hour
        minute = now.minute
        current = hour * 60 + minute

        morning_start = 9 * 60
        morning_end = 12 * 60
        afternoon_start = 13 * 60
        afternoon_end = 16 * 60

        if morning_start <= current < morning_end:
            return "morning"
        elif afternoon_start <= current < afternoon_end:
            return "afternoon"
        else:
            return "closed"

    def get_current_time_wib(self) -> str:
        now = datetime.now(self.tz)
        return now.strftime("%H:%M WIB")

    def get_indicators(self, symbol: str, df) -> dict:
        if df.empty or len(df) < 30:
            return {}

        volume_analysis = self.volume_ind.analyze(df)
        trend_analysis = self.trend_ind.analyze(df)
        momentum_analysis = self.momentum_ind.analyze(df)
        volatility_analysis = self.volatility_ind.analyze(df)

        return {
            "price": df["close"].iloc[-1],
            "volume_ratio": volume_analysis.get("volume_ratio", 1.0),
            "is_volume_spike": volume_analysis.get("is_volume_spike", False),
            "rsi": momentum_analysis.get("rsi", 50),
            "macd_bullish": momentum_analysis.get("bullish", False),
            "macd_histogram": momentum_analysis.get("macd_histogram", 0),
            "trend": trend_analysis.get("trend", "unknown"),
            "uptrend": trend_analysis.get("uptrend", False),
            "ema_fast": trend_analysis.get("ema_fast", 0),
            "ema_slow": trend_analysis.get("ema_slow", 0),
            "bb_position": volatility_analysis.get("position", "unknown"),
            "atr": volatility_analysis.get("atr", 0),
        }

    def scan_stock(self, symbol: str) -> Optional[Dict[str, Any]]:
        session = self.get_current_session()
        if session == "closed":
            return None

        try:
            df = self.collector.get_stock_data(symbol, days=60, timeframe="15m")
            if df.empty:
                return None

            indicators = self.get_indicators(symbol, df)
            if not indicators:
                return None

            current_time = self.get_current_time_wib()
            glm_result = self.glm.analyze_stock(symbol, indicators, session, current_time)

            glm_result["indicators"] = indicators
            glm_result["session"] = session
            glm_result["timestamp"] = datetime.now(self.tz).isoformat()

            return glm_result

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            return None

    def scan_all(self) -> List[Dict[str, Any]]:
        results = []
        for symbol in self.watchlist:
            result = self.scan_stock(symbol)
            if result and result.get("action") in ["BUY", "SELL"]:
                results.append(result)
        return results

    def scan_for_group(self) -> List[Dict[str, Any]]:
        results = self.scan_all()
        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return results
