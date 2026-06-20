import pandas as pd
import numpy as np
from typing import Tuple


class VolumeIndicator:
    def __init__(self, lookback_period: int = 20, spike_threshold: float = 2.0):
        self.lookback_period = lookback_period
        self.spike_threshold = spike_threshold

    def calculate_avg_volume(self, df: pd.DataFrame) -> pd.Series:
        return df["volume"].rolling(window=self.lookback_period).mean()

    def detect_volume_spike(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["avg_volume"] = self.calculate_avg_volume(df)
        df["volume_ratio"] = df["volume"] / df["avg_volume"]
        df["volume_spike"] = df["volume_ratio"] > self.spike_threshold
        return df

    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        obv = [0]
        for i in range(1, len(df)):
            if df["close"].iloc[i] > df["close"].iloc[i - 1]:
                obv.append(obv[-1] + df["volume"].iloc[i])
            elif df["close"].iloc[i] < df["close"].iloc[i - 1]:
                obv.append(obv[-1] - df["volume"].iloc[i])
            else:
                obv.append(obv[-1])
        return pd.Series(obv, index=df.index, name="obv")

    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        cumulative_tpv = (typical_price * df["volume"]).cumsum()
        cumulative_volume = df["volume"].cumsum()
        return cumulative_tpv / cumulative_volume

    def analyze(self, df: pd.DataFrame) -> dict:
        df = self.detect_volume_spike(df)

        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row

        obv = self.calculate_obv(df)
        obv_trend = "up" if obv.iloc[-1] > obv.iloc[-2] else "down" if len(obv) > 1 else "neutral"

        vwap = self.calculate_vwap(df)
        above_vwap = last_row["close"] > vwap.iloc[-1]

        return {
            "volume": last_row["volume"],
            "avg_volume": last_row["avg_volume"],
            "volume_ratio": last_row["volume_ratio"],
            "is_volume_spike": last_row["volume_spike"],
            "obv_trend": obv_trend,
            "above_vwap": above_vwap,
            "volume_score": self._calculate_score(last_row["volume_ratio"], obv_trend, above_vwap),
        }

    def _calculate_score(self, volume_ratio: float, obv_trend: str, above_vwap: bool) -> int:
        score = 0

        if volume_ratio >= self.spike_threshold:
            score += 40
        elif volume_ratio >= 1.5:
            score += 20
        elif volume_ratio >= 1.0:
            score += 10

        if obv_trend == "up":
            score += 30
        elif obv_trend == "neutral":
            score += 15

        if above_vwap:
            score += 30
        else:
            score += 10

        return min(score, 100)
