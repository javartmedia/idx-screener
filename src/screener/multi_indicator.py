import pandas as pd
from datetime import datetime
from typing import List, Optional

from ..config import AppConfig
from ..data_models import StockData, Signal
from ..indicators import VolumeIndicator, TrendIndicator, MomentumIndicator, VolatilityIndicator
from .signal_scorer import SignalScorer


class MultiIndicatorScreener:
    def __init__(self, config: AppConfig):
        self.config = config
        self.volume_ind = VolumeIndicator(
            lookback_period=config.indicators.volume.lookback_period,
            spike_threshold=config.indicators.volume.spike_threshold,
        )
        self.trend_ind = TrendIndicator(
            ema_fast=config.indicators.trend.ema_fast,
            ema_slow=config.indicators.trend.ema_slow,
            adx_threshold=config.indicators.trend.adx_threshold,
        )
        self.momentum_ind = MomentumIndicator(
            rsi_period=config.indicators.momentum.rsi_period,
            rsi_oversold=config.indicators.momentum.rsi_oversold,
            rsi_overbought=config.indicators.momentum.rsi_overbought,
            macd_fast=config.indicators.momentum.macd_fast,
            macd_slow=config.indicators.momentum.macd_slow,
            macd_signal=config.indicators.momentum.macd_signal,
        )
        self.volatility_ind = VolatilityIndicator(
            bb_period=config.indicators.volatility.bb_period,
            bb_std=config.indicators.volatility.bb_std,
            atr_period=config.indicators.volatility.atr_period,
        )
        self.scorer = SignalScorer(config)

    def analyze_stock(self, stock_data: StockData) -> dict:
        if stock_data.data.empty or len(stock_data.data) < 30:
            return {"error": "Insufficient data", "symbol": stock_data.symbol}

        df = stock_data.data

        volume_analysis = self.volume_ind.analyze(df)
        trend_analysis = self.trend_ind.analyze(df)
        momentum_analysis = self.momentum_ind.analyze(df)
        volatility_analysis = self.volatility_ind.analyze(df)

        all_indicators = {
            **volume_analysis,
            **trend_analysis,
            **momentum_analysis,
            **volatility_analysis,
        }

        signal_details = self.scorer.get_signal_details(all_indicators)

        return {
            "symbol": stock_data.symbol,
            "last_price": stock_data.last_price,
            "change_percent": stock_data.change_percent,
            "indicators": all_indicators,
            "signal": signal_details,
            "timestamp": datetime.now().isoformat(),
        }

    def screen_stock(self, symbol: str, df: pd.DataFrame) -> Optional[Signal]:
        stock_data = StockData.from_dataframe(symbol, df)
        analysis = self.analyze_stock(stock_data)

        if "error" in analysis:
            return None

        signal_info = analysis["signal"]

        if not signal_info["is_valid"]:
            return None

        entry_price = stock_data.last_price
        atr_stops = analysis["indicators"].get("atr", {})

        risk_mgmt = self.config.risk_management
        if risk_mgmt.stop_loss.method == "atr":
            stop_loss = entry_price - (risk_mgmt.stop_loss.atr_multiplier * analysis["indicators"].get("atr", entry_price * 0.02))
        else:
            stop_loss = entry_price * 0.98

        take_profit = entry_price + (risk_mgmt.take_profit.ratio * (entry_price - stop_loss))

        indicators_summary = {
            "volume_ratio": analysis["indicators"].get("volume_ratio", 0),
            "rsi": analysis["indicators"].get("rsi", 50),
            "macd_bullish": analysis["indicators"].get("bullish", False),
            "trend": analysis["indicators"].get("trend", "unknown"),
            "bb_position": analysis["indicators"].get("position", "unknown"),
        }

        message = self._generate_signal_message(analysis, signal_info)

        return Signal(
            symbol=symbol,
            signal_type="BUY",
            score=signal_info["total_score"],
            entry_price=entry_price,
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            timestamp=datetime.now(),
            indicators=indicators_summary,
            message=message,
        )

    def _generate_signal_message(self, analysis: dict, signal_info: dict) -> str:
        symbol = analysis["symbol"]
        score = signal_info["total_score"]
        strength = signal_info["strength"]
        price = analysis["last_price"]

        parts = [
            f"🔔 {strength} BUY SIGNAL - {symbol}",
            f"💰 Entry: Rp {price:,.0f}",
            f"📊 Score: {score}/100",
            "",
            "Indikator:",
        ]

        indicators = analysis["indicators"]

        if indicators.get("is_volume_spike"):
            parts.append(f"✅ Volume: {indicators.get('volume_ratio', 0):.1f}x average")
        else:
            parts.append(f"⚠️ Volume: {indicators.get('volume_ratio', 0):.1f}x average")

        rsi = indicators.get("rsi", 50)
        if 30 < rsi < 70:
            parts.append(f"✅ RSI: {rsi:.0f} (Neutral)")
        elif rsi <= 30:
            parts.append(f"✅ RSI: {rsi:.0f} (Oversold)")
        else:
            parts.append(f"⚠️ RSI: {rsi:.0f} (Overbought)")

        if indicators.get("bullish"):
            parts.append("✅ MACD: Bullish")
        else:
            parts.append("⚠️ MACD: Bearish")

        if indicators.get("uptrend"):
            parts.append("✅ Trend: Uptrend")
        else:
            parts.append("⚠️ Trend: Downtrend")

        return "\n".join(parts)

    def screen_multiple(self, stocks: dict) -> List[Signal]:
        signals = []

        for symbol, df in stocks.items():
            signal = self.screen_stock(symbol, df)
            if signal:
                signals.append(signal)

        signals.sort(key=lambda x: x.score, reverse=True)
        return signals
