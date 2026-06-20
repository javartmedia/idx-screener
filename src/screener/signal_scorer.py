from ..config import AppConfig


class SignalScorer:
    def __init__(self, config: AppConfig):
        self.weights = config.signal_scoring.weights
        self.min_score = config.signal_scoring.min_score

    def calculate_total_score(self, indicators: dict) -> int:
        volume_score = indicators.get("volume_score", 0)
        trend_score = indicators.get("trend_score", 0)
        momentum_score = indicators.get("momentum_score", 0)
        volatility_score = indicators.get("volatility_score", 0)

        weighted_volume = (volume_score * self.weights.get("volume", 30)) / 100
        weighted_trend = (trend_score * self.weights.get("trend", 25)) / 100
        weighted_momentum_rsi = (indicators.get("rsi_score", 0) * self.weights.get("rsi", 20)) / 100
        weighted_momentum_macd = (indicators.get("macd_score", 0) * self.weights.get("macd", 15)) / 100
        weighted_volatility = (volatility_score * self.weights.get("bollinger", 10)) / 100

        total = (
            weighted_volume +
            weighted_trend +
            weighted_momentum_rsi +
            weighted_momentum_macd +
            weighted_volatility
        )

        return int(min(total, 100))

    def get_signal_strength(self, score: int) -> str:
        if score >= 80:
            return "STRONG"
        elif score >= 60:
            return "MEDIUM"
        elif score >= 40:
            return "WEAK"
        else:
            return "NO_SIGNAL"

    def is_valid_signal(self, score: int) -> bool:
        return score >= self.min_score

    def get_signal_details(self, indicators: dict) -> dict:
        total_score = self.calculate_total_score(indicators)
        strength = self.get_signal_strength(total_score)
        is_valid = self.is_valid_signal(total_score)

        return {
            "total_score": total_score,
            "strength": strength,
            "is_valid": is_valid,
            "min_score_required": self.min_score,
            "breakdown": {
                "volume": indicators.get("volume_score", 0),
                "trend": indicators.get("trend_score", 0),
                "rsi": indicators.get("rsi_score", 0),
                "macd": indicators.get("macd_score", 0),
                "volatility": indicators.get("volatility_score", 0),
            }
        }
