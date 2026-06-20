import math
from typing import Optional

from ..config import AppConfig


class PositionSizer:
    def __init__(self, config: AppConfig):
        self.capital = config.risk_management.capital
        self.risk_per_trade = config.risk_management.risk_per_trade
        self.max_positions = config.risk_management.max_positions
        self.max_daily_loss = config.risk_management.max_daily_loss

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        method: str = "fixed_risk"
    ) -> dict:
        if method == "fixed_risk":
            return self._fixed_risk_sizing(entry_price, stop_loss)
        elif method == "atr":
            return self._atr_sizing(entry_price, stop_loss)
        elif method == "kelly":
            return self._kelly_sizing(entry_price, stop_loss)
        else:
            return self._fixed_risk_sizing(entry_price, stop_loss)

    def _fixed_risk_sizing(self, entry_price: float, stop_loss: float) -> dict:
        risk_amount = self.capital * self.risk_per_trade

        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            return {"quantity": 0, "risk_amount": 0, "position_value": 0}

        quantity = math.floor(risk_amount / risk_per_share)
        quantity = self._round_to_lot(quantity)

        position_value = quantity * entry_price
        actual_risk = quantity * risk_per_share

        return {
            "quantity": quantity,
            "risk_amount": actual_risk,
            "position_value": position_value,
            "risk_percent": (actual_risk / self.capital) * 100,
            "position_percent": (position_value / self.capital) * 100,
        }

    def _atr_sizing(self, entry_price: float, stop_loss: float) -> dict:
        return self._fixed_risk_sizing(entry_price, stop_loss)

    def _kelly_sizing(self, entry_price: float, stop_loss: float) -> dict:
        return self._fixed_risk_sizing(entry_price, stop_loss)

    def _round_to_lot(self, quantity: int) -> int:
        lot_size = 100
        return (quantity // lot_size) * lot_size

    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: Optional[float] = None,
        method: str = "atr",
        multiplier: float = 1.5
    ) -> float:
        if method == "atr" and atr is not None:
            return entry_price - (multiplier * atr)
        elif method == "percentage":
            return entry_price * 0.98
        else:
            return entry_price * 0.98

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        ratio: float = 2.0
    ) -> float:
        risk = entry_price - stop_loss
        return entry_price + (ratio * risk)

    def validate_position(self, position_value: float, current_positions: int) -> dict:
        checks = {
            "max_positions": current_positions < self.max_positions,
            "max_position_size": position_value <= self.capital * 0.3,
            "min_position_size": position_value >= 100000,
        }

        checks["all_passed"] = all(checks.values())

        return checks

    def get_risk_summary(self) -> dict:
        return {
            "capital": self.capital,
            "risk_per_trade": self.risk_per_trade,
            "max_risk_amount": self.capital * self.risk_per_trade,
            "max_positions": self.max_positions,
            "max_daily_loss": self.max_daily_loss,
            "max_daily_loss_amount": self.capital * self.max_daily_loss,
        }
