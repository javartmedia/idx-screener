import pandas as pd
import numpy as np
from typing import Dict, Tuple
from datetime import datetime, timedelta


class PredictionIndicator:
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days

    def predict_price(self, df: pd.DataFrame, days_ahead: int = 1) -> Dict:
        if len(df) < 20:
            return self._default_prediction()

        close_prices = df["close"].values
        high_prices = df["high"].values
        low_prices = df["low"].values

        sma_5 = self._calculate_sma(close_prices, 5)
        sma_10 = self._calculate_sma(close_prices, 10)
        sma_20 = self._calculate_sma(close_prices, 20)

        momentum = self._calculate_momentum(close_prices, 10)
        volatility = self._calculate_volatility(close_prices, 20)

        support, resistance = self._identify_support_resistance(
            high_prices, low_prices, close_prices
        )

        last_close = close_prices[-1]
        trend_factor = self._calculate_trend_factor(sma_5, sma_10, sma_20)
        momentum_factor = momentum / last_close

        predicted_change = (trend_factor * 0.4 + momentum_factor * 0.3) * last_close
        predicted_mid = last_close + predicted_change

        price_range = volatility * last_close * np.sqrt(days_ahead)
        predicted_low = predicted_mid - price_range * 0.6
        predicted_high = predicted_mid + price_range * 0.6

        confidence = self._calculate_confidence(
            df, trend_factor, volatility, momentum
        )

        return {
            "current_price": round(last_close, 0),
            "predicted_low": round(predicted_low, 0),
            "predicted_mid": round(predicted_mid, 0),
            "predicted_high": round(predicted_high, 0),
            "confidence": round(confidence, 1),
            "support_1": round(support[0], 0) if len(support) > 0 else round(last_close * 0.97, 0),
            "support_2": round(support[1], 0) if len(support) > 1 else round(last_close * 0.94, 0),
            "resistance_1": round(resistance[0], 0) if len(resistance) > 0 else round(last_close * 1.03, 0),
            "resistance_2": round(resistance[1], 0) if len(resistance) > 1 else round(last_close * 1.06, 0),
            "trend": self._get_trend(sma_5, sma_10, sma_20),
            "momentum": "Bullish" if momentum > 0 else "Bearish",
            "expected_change_pct": round((predicted_mid - last_close) / last_close * 100, 2),
        }

    def _calculate_sma(self, data: np.ndarray, period: int) -> float:
        if len(data) < period:
            return data[-1]
        return np.mean(data[-period:])

    def _calculate_momentum(self, data: np.ndarray, period: int) -> float:
        if len(data) < period:
            return 0
        return data[-1] - data[-period]

    def _calculate_volatility(self, data: np.ndarray, period: int) -> float:
        if len(data) < period:
            return 0.02
        returns = np.diff(data[-period:]) / data[-period:-1]
        return np.std(returns)

    def _identify_support_resistance(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray
    ) -> Tuple[list, list]:
        supports = []
        resistances = []

        for i in range(2, len(closes) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                supports.append(lows[i])
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                resistances.append(highs[i])

        supports = sorted(supports)[-2:] if len(supports) >= 2 else supports
        resistances = sorted(resistances)[-2:] if len(resistances) >= 2 else resistances

        if not supports:
            supports = [np.min(lows[-20:]) * 1.01]
        if not resistances:
            resistances = [np.max(highs[-20:]) * 0.99]

        return supports, resistances

    def _calculate_trend_factor(self, sma_5: float, sma_10: float, sma_20: float) -> float:
        if sma_5 > sma_10 > sma_20:
            return 0.02
        elif sma_5 > sma_10:
            return 0.01
        elif sma_5 < sma_10 < sma_20:
            return -0.02
        elif sma_5 < sma_10:
            return -0.01
        return 0.0

    def _calculate_confidence(
        self, df: pd.DataFrame, trend_factor: float, volatility: float, momentum: float
    ) -> float:
        confidence = 50.0

        if abs(trend_factor) > 0.015:
            confidence += 15
        elif abs(trend_factor) > 0.005:
            confidence += 10

        if volatility < 0.02:
            confidence += 10
        elif volatility < 0.03:
            confidence += 5

        if abs(momentum) > df["close"].iloc[-1] * 0.02:
            confidence += 10

        volume = df["volume"].values
        if len(volume) > 5:
            avg_vol = np.mean(volume[-5:])
            if volume[-1] > avg_vol * 1.5:
                confidence += 5

        return min(confidence, 95)

    def _get_trend(self, sma_5: float, sma_10: float, sma_20: float) -> str:
        if sma_5 > sma_10 > sma_20:
            return "Strong Uptrend"
        elif sma_5 > sma_10:
            return "Uptrend"
        elif sma_5 < sma_10 < sma_20:
            return "Strong Downtrend"
        elif sma_5 < sma_10:
            return "Downtrend"
        return "Sideways"

    def _default_prediction(self) -> Dict:
        return {
            "current_price": 0,
            "predicted_low": 0,
            "predicted_mid": 0,
            "predicted_high": 0,
            "confidence": 0,
            "support_1": 0,
            "support_2": 0,
            "resistance_1": 0,
            "resistance_2": 0,
            "trend": "Unknown",
            "momentum": "Unknown",
            "expected_change_pct": 0,
        }
