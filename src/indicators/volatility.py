import pandas as pd
import numpy as np
from typing import Tuple


class VolatilityIndicator:
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, atr_period: int = 14):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.atr_period = atr_period

    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["bb_middle"] = df["close"].rolling(window=self.bb_period).mean()
        df["bb_std"] = df["close"].rolling(window=self.bb_period).std()

        df["bb_upper"] = df["bb_middle"] + (self.bb_std * df["bb_std"])
        df["bb_lower"] = df["bb_middle"] - (self.bb_std * df["bb_std"])

        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
        df["bb_percent"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

        return df

    def analyze_bollinger(self, df: pd.DataFrame) -> dict:
        bb_df = self.calculate_bollinger_bands(df)

        current_close = bb_df["close"].iloc[-1]
        bb_upper = bb_df["bb_upper"].iloc[-1]
        bb_lower = bb_df["bb_lower"].iloc[-1]
        bb_middle = bb_df["bb_middle"].iloc[-1]
        bb_width = bb_df["bb_width"].iloc[-1]
        bb_percent = bb_df["bb_percent"].iloc[-1]

        prev_close = bb_df["close"].iloc[-2] if len(bb_df) > 1 else current_close
        prev_upper = bb_df["bb_upper"].iloc[-2] if len(bb_df) > 1 else bb_upper
        prev_lower = bb_df["bb_lower"].iloc[-2] if len(bb_df) > 1 else bb_lower

        breakout_upper = current_close > bb_upper and prev_close <= prev_upper
        breakout_lower = current_close < bb_lower and prev_close >= prev_lower

        if bb_percent > 1:
            position = "above_upper"
        elif bb_percent < 0:
            position = "below_lower"
        elif bb_percent > 0.8:
            position = "near_upper"
        elif bb_percent < 0.2:
            position = "near_lower"
        else:
            position = "middle"

        avg_width = bb_df["bb_width"].rolling(window=50).mean().iloc[-1] if len(bb_df) >= 50 else bb_width
        squeeze = bb_width < avg_width * 0.75

        return {
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "bb_middle": bb_middle,
            "bb_width": bb_width,
            "bb_percent": bb_percent,
            "breakout_upper": breakout_upper,
            "breakout_lower": breakout_lower,
            "position": position,
            "squeeze": squeeze,
        }

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        df = df.copy()

        df["tr"] = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                abs(df["high"] - df["close"].shift(1)),
                abs(df["low"] - df["close"].shift(1))
            )
        )

        atr = df["tr"].rolling(window=self.atr_period).mean()
        return atr

    def calculate_keltner_channels(self, df: pd.DataFrame, ema_period: int = 20, atr_multiplier: float = 2.0) -> pd.DataFrame:
        df = df.copy()

        df["kc_middle"] = df["close"].ewm(span=ema_period, adjust=False).mean()
        atr = self.calculate_atr(df)

        df["kc_upper"] = df["kc_middle"] + (atr_multiplier * atr)
        df["kc_lower"] = df["kc_middle"] - (atr_multiplier * atr)

        return df

    def detect_squeeze(self, df: pd.DataFrame) -> dict:
        bb_df = self.calculate_bollinger_bands(df)
        kc_df = self.calculate_keltner_channels(df)

        bb_upper = bb_df["bb_upper"].iloc[-1]
        bb_lower = bb_df["bb_lower"].iloc[-1]
        kc_upper = kc_df["kc_upper"].iloc[-1]
        kc_lower = kc_df["kc_lower"].iloc[-1]

        squeeze_on = bb_lower > kc_lower and bb_upper < kc_upper
        squeeze_off = not squeeze_on

        prev_squeeze = bb_df["bb_lower"].iloc[-2] > kc_df["kc_lower"].iloc[-2] if len(df) > 1 else False
        just_released = prev_squeeze and squeeze_off

        return {
            "squeeze_on": squeeze_on,
            "squeeze_off": squeeze_off,
            "just_released": just_released,
        }

    def calculate_atr_stops(self, df: pd.DataFrame, multiplier: float = 1.5) -> dict:
        atr = self.calculate_atr(df)
        current_atr = atr.iloc[-1]
        current_close = df["close"].iloc[-1]

        return {
            "atr": current_atr,
            "stop_loss": current_close - (multiplier * current_atr),
            "take_profit": current_close + (2 * multiplier * current_atr),
        }

    def analyze(self, df: pd.DataFrame) -> dict:
        bb_data = self.analyze_bollinger(df)
        squeeze_data = self.detect_squeeze(df)
        atr_stops = self.calculate_atr_stops(df)

        score = self._calculate_score(bb_data, squeeze_data)

        return {
            **bb_data,
            **squeeze_data,
            **atr_stops,
            "volatility_score": score,
        }

    def _calculate_score(self, bb: dict, squeeze: dict) -> int:
        score = 0

        if bb["breakout_upper"]:
            score += 40
        elif bb["position"] == "near_upper":
            score += 25
        elif bb["position"] == "middle":
            score += 15

        if squeeze["just_released"]:
            score += 35
        elif squeeze["squeeze_off"]:
            score += 20

        if bb["bb_percent"] > 0.5:
            score += 25
        elif bb["bb_percent"] > 0.3:
            score += 15

        return min(score, 100)
