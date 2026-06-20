import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


class VolumeAnalysis:
    def __init__(self, lookback_days: int = 7):
        self.lookback_days = lookback_days

    def analyze(self, df: pd.DataFrame) -> Dict:
        if len(df) < 10:
            return self._default_analysis()

        volumes = df["volume"].values
        closes = df["close"].values

        volume_stats = self._calculate_volume_stats(volumes)
        volume_trend = self._analyze_volume_trend(volumes)
        obv_analysis = self._calculate_obv(closes, volumes)
        accumulation = self._detect_accumulation(closes, volumes)
        volume_prediction = self._predict_next_volume(volumes)
        volume_spikes = self._detect_volume_spikes(volumes)

        return {
            "avg_volume": volume_stats["avg"],
            "max_volume": volume_stats["max"],
            "min_volume": volume_stats["min"],
            "max_volume_day": volume_stats["max_day"],
            "min_volume_day": volume_stats["min_day"],
            "volume_trend": volume_trend["trend"],
            "trend_strength": volume_trend["strength"],
            "obv_trend": obv_analysis["trend"],
            "obv_value": obv_analysis["value"],
            "accumulation_phase": accumulation["phase"],
            "accumulation_signal": accumulation["signal"],
            "predicted_volume": volume_prediction["predicted"],
            "volume_condition": volume_prediction["condition"],
            "has_spike": volume_spikes["has_spike"],
            "spike_ratio": volume_spikes["ratio"],
            "volume_score": self._calculate_score(
                volume_trend, obv_analysis, accumulation, volume_spikes
            ),
        }

    def _calculate_volume_stats(self, volumes: np.ndarray) -> Dict:
        recent = volumes[-self.lookback_days:]
        avg_vol = np.mean(recent)
        max_vol = np.max(recent)
        min_vol = np.min(recent)
        max_day = np.argmax(recent) + 1
        min_day = np.argmin(recent) + 1

        return {
            "avg": int(avg_vol),
            "max": int(max_vol),
            "min": int(min_vol),
            "max_day": f"H-{self.lookback_days - max_day + 1}",
            "min_day": f"H-{self.lookback_days - min_day + 1}",
        }

    def _analyze_volume_trend(self, volumes: np.ndarray) -> Dict:
        recent = volumes[-self.lookback_days:]
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent, 1)[0]

        avg_vol = np.mean(recent)
        normalized_slope = slope / avg_vol if avg_vol > 0 else 0

        if normalized_slope > 0.05:
            trend = "Increasing"
            strength = "Strong"
        elif normalized_slope > 0.02:
            trend = "Increasing"
            strength = "Moderate"
        elif normalized_slope < -0.05:
            trend = "Decreasing"
            strength = "Strong"
        elif normalized_slope < -0.02:
            trend = "Decreasing"
            strength = "Moderate"
        else:
            trend = "Stable"
            strength = "Normal"

        return {
            "trend": trend,
            "strength": strength,
            "slope": round(normalized_slope * 100, 2),
        }

    def _calculate_obv(self, closes: np.ndarray, volumes: np.ndarray) -> Dict:
        obv = [0]
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv.append(obv[-1] + volumes[i])
            elif closes[i] < closes[i-1]:
                obv.append(obv[-1] - volumes[i])
            else:
                obv.append(obv[-1])

        obv_array = np.array(obv)
        recent_obv = obv_array[-self.lookback_days:]

        if len(recent_obv) > 1:
            if recent_obv[-1] > recent_obv[0]:
                trend = "Up"
            elif recent_obv[-1] < recent_obv[0]:
                trend = "Down"
            else:
                trend = "Flat"
        else:
            trend = "Flat"

        return {
            "trend": trend,
            "value": int(obv_array[-1]),
        }

    def _detect_accumulation(self, closes: np.ndarray, volumes: np.ndarray) -> Dict:
        recent_closes = closes[-self.lookback_days:]
        recent_volumes = volumes[-self.lookback_days:]

        price_change = (recent_closes[-1] - recent_closes[0]) / recent_closes[0]
        avg_volume = np.mean(recent_volumes)
        recent_avg_volume = np.mean(recent_volumes[-3:])

        if price_change > 0 and recent_avg_volume > avg_volume:
            phase = "Accumulation"
            signal = "Bullish"
        elif price_change < 0 and recent_avg_volume > avg_volume:
            phase = "Distribution"
            signal = "Bearish"
        elif price_change > 0 and recent_avg_volume < avg_volume:
            phase = "Quiet Uptrend"
            signal = "Neutral"
        elif price_change < 0 and recent_avg_volume < avg_volume:
            phase = "Quiet Downtrend"
            signal = "Neutral"
        else:
            phase = "Consolidation"
            signal = "Neutral"

        return {
            "phase": phase,
            "signal": signal,
        }

    def _predict_next_volume(self, volumes: np.ndarray) -> Dict:
        recent = volumes[-self.lookback_days:]
        avg_vol = np.mean(recent)
        last_vol = volumes[-1]

        x = np.arange(len(recent))
        slope = np.polyfit(x, recent, 1)[0]

        predicted = int(avg_vol + slope)

        if last_vol > avg_vol * 1.5:
            condition = "High activity anticipated"
        elif last_vol > avg_vol * 1.2:
            condition = "Above average activity"
        elif last_vol < avg_vol * 0.7:
            condition = "Low activity expected"
        else:
            condition = "Normal activity expected"

        return {
            "predicted": predicted,
            "condition": condition,
        }

    def _detect_volume_spikes(self, volumes: np.ndarray) -> Dict:
        if len(volumes) < 5:
            return {"has_spike": False, "ratio": 1.0}

        avg_vol = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
        last_vol = volumes[-1]

        ratio = last_vol / avg_vol if avg_vol > 0 else 1.0
        has_spike = ratio > 1.5

        return {
            "has_spike": has_spike,
            "ratio": round(ratio, 2),
        }

    def _calculate_score(
        self, volume_trend: Dict, obv: Dict, accumulation: Dict, spikes: Dict
    ) -> int:
        score = 0

        if volume_trend["trend"] == "Increasing":
            score += 30
        elif volume_trend["trend"] == "Stable":
            score += 15

        if obv["trend"] == "Up":
            score += 25
        elif obv["trend"] == "Flat":
            score += 10

        if accumulation["signal"] == "Bullish":
            score += 25
        elif accumulation["signal"] == "Neutral":
            score += 10

        if spikes["has_spike"]:
            score += 20
        elif spikes["ratio"] > 1.2:
            score += 10

        return min(score, 100)

    def _default_analysis(self) -> Dict:
        return {
            "avg_volume": 0,
            "max_volume": 0,
            "min_volume": 0,
            "max_volume_day": "N/A",
            "min_volume_day": "N/A",
            "volume_trend": "Unknown",
            "trend_strength": "Unknown",
            "obv_trend": "Unknown",
            "obv_value": 0,
            "accumulation_phase": "Unknown",
            "accumulation_signal": "Unknown",
            "predicted_volume": 0,
            "volume_condition": "Unknown",
            "has_spike": False,
            "spike_ratio": 1.0,
            "volume_score": 0,
        }
