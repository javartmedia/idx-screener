import pandas as pd
import numpy as np
from typing import Tuple


class MomentumIndicator:
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
    ):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal

    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        delta = df["close"].diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def analyze_rsi(self, df: pd.DataFrame) -> dict:
        rsi = self.calculate_rsi(df)
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi

        if current_rsi < self.rsi_oversold:
            zone = "oversold"
        elif current_rsi > self.rsi_overbought:
            zone = "overbought"
        else:
            zone = "neutral"

        rising = current_rsi > prev_rsi
        falling = current_rsi < prev_rsi

        return {
            "rsi": current_rsi,
            "prev_rsi": prev_rsi,
            "zone": zone,
            "rising": rising,
            "falling": falling,
        }

    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        ema_fast = df["close"].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.macd_slow, adjust=False).mean()

        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=self.macd_signal, adjust=False).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        return df

    def analyze_macd(self, df: pd.DataFrame) -> dict:
        macd_df = self.calculate_macd(df)

        current_macd = macd_df["macd"].iloc[-1]
        current_signal = macd_df["macd_signal"].iloc[-1]
        current_histogram = macd_df["macd_histogram"].iloc[-1]

        prev_macd = macd_df["macd"].iloc[-2] if len(macd_df) > 1 else current_macd
        prev_signal = macd_df["macd_signal"].iloc[-2] if len(macd_df) > 1 else current_signal

        bullish_cross = prev_macd <= prev_signal and current_macd > current_signal
        bearish_cross = prev_macd >= prev_signal and current_macd < current_signal

        bullish = current_macd > current_signal
        histogram_positive = current_histogram > 0
        histogram_increasing = current_histogram > prev_histogram if len(macd_df) > 1 else False

        return {
            "macd": current_macd,
            "macd_signal": current_signal,
            "macd_histogram": current_histogram,
            "bullish_cross": bullish_cross,
            "bearish_cross": bearish_cross,
            "bullish": bullish,
            "histogram_positive": histogram_positive,
            "histogram_increasing": histogram_increasing,
        }

    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        df = df.copy()

        low_min = df["low"].rolling(window=k_period).min()
        high_max = df["high"].rolling(window=k_period).max()

        df["stoch_k"] = 100 * (df["close"] - low_min) / (high_max - low_min)
        df["stoch_d"] = df["stoch_k"].rolling(window=d_period).mean()

        return df

    def analyze_stochastic(self, df: pd.DataFrame) -> dict:
        stoch_df = self.calculate_stochastic(df)

        current_k = stoch_df["stoch_k"].iloc[-1]
        current_d = stoch_df["stoch_d"].iloc[-1]

        if current_k < 20:
            zone = "oversold"
        elif current_k > 80:
            zone = "overbought"
        else:
            zone = "neutral"

        bullish_cross = current_k > current_d and stoch_df["stoch_k"].iloc[-2] <= stoch_df["stoch_d"].iloc[-2]

        return {
            "stoch_k": current_k,
            "stoch_d": current_d,
            "zone": zone,
            "bullish_cross": bullish_cross,
        }

    def analyze(self, df: pd.DataFrame) -> dict:
        rsi_data = self.analyze_rsi(df)
        macd_data = self.analyze_macd(df)
        stoch_data = self.analyze_stochastic(df)

        score = self._calculate_score(rsi_data, macd_data, stoch_data)

        return {
            **rsi_data,
            **macd_data,
            **stoch_data,
            "momentum_score": score,
        }

    def _calculate_score(self, rsi: dict, macd: dict, stoch: dict) -> int:
        score = 0

        if rsi["zone"] == "oversold":
            score += 30
        elif rsi["zone"] == "neutral" and rsi["rising"]:
            score += 20
        elif rsi["zone"] == "neutral":
            score += 10

        if macd["bullish_cross"]:
            score += 35
        elif macd["bullish"] and macd["histogram_increasing"]:
            score += 25
        elif macd["bullish"]:
            score += 15

        if stoch["zone"] == "oversold" and stoch["bullish_cross"]:
            score += 20
        elif stoch["zone"] == "oversold":
            score += 15
        elif stoch["zone"] == "neutral":
            score += 10

        return min(score, 100)
