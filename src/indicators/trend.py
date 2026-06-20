import pandas as pd
import numpy as np
from typing import Tuple


class TrendIndicator:
    def __init__(self, ema_fast: int = 9, ema_slow: int = 21, adx_threshold: int = 25):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.adx_threshold = adx_threshold

    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        return df["close"].ewm(span=period, adjust=False).mean()

    def calculate_sma(self, df: pd.DataFrame, period: int) -> pd.Series:
        return df["close"].rolling(window=period).mean()

    def detect_ema_cross(self, df: pd.DataFrame) -> dict:
        ema_fast = self.calculate_ema(df, self.ema_fast)
        ema_slow = self.calculate_ema(df, self.ema_slow)

        current_fast = ema_fast.iloc[-1]
        current_slow = ema_slow.iloc[-1]
        prev_fast = ema_fast.iloc[-2] if len(ema_fast) > 1 else current_fast
        prev_slow = ema_slow.iloc[-2] if len(ema_slow) > 1 else current_slow

        bullish_cross = prev_fast <= prev_slow and current_fast > current_slow
        bearish_cross = prev_fast >= prev_slow and current_fast < current_slow
        uptrend = current_fast > current_slow

        return {
            "ema_fast": current_fast,
            "ema_slow": current_slow,
            "bullish_cross": bullish_cross,
            "bearish_cross": bearish_cross,
            "uptrend": uptrend,
        }

    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        df = df.copy()

        df["tr"] = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                abs(df["high"] - df["close"].shift(1)),
                abs(df["low"] - df["close"].shift(1))
            )
        )

        df["plus_dm"] = np.where(
            (df["high"] - df["high"].shift(1)) > (df["low"].shift(1) - df["low"]),
            np.maximum(df["high"] - df["high"].shift(1), 0),
            0
        )

        df["minus_dm"] = np.where(
            (df["low"].shift(1) - df["low"]) > (df["high"] - df["high"].shift(1)),
            np.maximum(df["low"].shift(1) - df["low"], 0),
            0
        )

        df["atr"] = df["tr"].rolling(window=period).mean()
        df["plus_di"] = 100 * (df["plus_dm"].rolling(window=period).mean() / df["atr"])
        df["minus_di"] = 100 * (df["minus_dm"].rolling(window=period).mean() / df["atr"])

        df["dx"] = 100 * abs(df["plus_di"] - df["minus_di"]) / (df["plus_di"] + df["minus_di"])
        df["adx"] = df["dx"].rolling(window=period).mean()

        return df

    def detect_trend_strength(self, df: pd.DataFrame) -> dict:
        adx_df = self.calculate_adx(df)

        current_adx = adx_df["adx"].iloc[-1]
        plus_di = adx_df["plus_di"].iloc[-1]
        minus_di = adx_df["minus_di"].iloc[-1]

        if current_adx > self.adx_threshold:
            if plus_di > minus_di:
                trend = "strong_uptrend"
            else:
                trend = "strong_downtrend"
        elif current_adx > 20:
            if plus_di > minus_di:
                trend = "weak_uptrend"
            else:
                trend = "weak_downtrend"
        else:
            trend = "no_trend"

        return {
            "adx": current_adx,
            "plus_di": plus_di,
            "minus_di": minus_di,
            "trend": trend,
            "strong_trend": current_adx > self.adx_threshold,
        }

    def calculate_slope(self, df: pd.DataFrame, period: int = 20) -> float:
        if len(df) < period:
            return 0.0

        y = df["close"].iloc[-period:].values
        x = np.arange(period)

        slope = np.polyfit(x, y, 1)[0]
        return slope / y.mean() * 100

    def analyze(self, df: pd.DataFrame) -> dict:
        ema_cross = self.detect_ema_cross(df)
        trend_strength = self.detect_trend_strength(df)
        slope = self.calculate_slope(df)

        score = self._calculate_score(ema_cross, trend_strength, slope)

        return {
            **ema_cross,
            **trend_strength,
            "slope": slope,
            "trend_score": score,
        }

    def _calculate_score(self, ema_cross: dict, trend_strength: dict, slope: float) -> int:
        score = 0

        if ema_cross["uptrend"]:
            score += 40
        if ema_cross["bullish_cross"]:
            score += 20

        if trend_strength["strong_trend"]:
            score += 25
        elif trend_strength["trend"] in ["weak_uptrend", "weak_downtrend"]:
            score += 10

        if slope > 0.1:
            score += 15
        elif slope > 0:
            score += 10
        elif slope > -0.1:
            score += 5

        return min(score, 100)
