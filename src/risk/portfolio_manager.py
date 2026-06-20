from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field

from ..config import AppConfig
from ..data_models import TradeResult


class PortfolioManager:
    def __init__(self, config: AppConfig):
        self.capital = config.risk_management.capital
        self.max_positions = config.risk_management.max_positions
        self.trades: List[TradeResult] = []
        self.daily_pnl: float = 0.0

    def add_trade(self, trade: TradeResult) -> bool:
        if len(self.get_open_positions()) >= self.max_positions:
            return False

        self.trades.append(trade)
        return True

    def close_trade(self, symbol: str, exit_price: float) -> Optional[TradeResult]:
        for trade in self.trades:
            if trade.symbol == symbol and trade.status == "open":
                trade.close(datetime.now(), exit_price)
                self.daily_pnl += trade.pnl
                return trade
        return None

    def get_open_positions(self) -> List[TradeResult]:
        return [t for t in self.trades if t.status == "open"]

    def get_closed_positions(self) -> List[TradeResult]:
        return [t for t in self.trades if t.status == "closed"]

    def get_position_by_symbol(self, symbol: str) -> Optional[TradeResult]:
        for trade in self.trades:
            if trade.symbol == symbol and trade.status == "open":
                return trade
        return None

    def calculate_portfolio_metrics(self) -> dict:
        closed = self.get_closed_positions()
        open_positions = self.get_open_positions()

        total_trades = len(closed)
        winning_trades = len([t for t in closed if t.pnl > 0])
        losing_trades = len([t for t in closed if t.pnl <= 0])

        total_pnl = sum(t.pnl for t in closed)
        avg_win = sum(t.pnl for t in closed if t.pnl > 0) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(t.pnl for t in closed if t.pnl <= 0) / losing_trades if losing_trades > 0 else 0

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float("inf")

        total_invested = sum(t.entry_price * t.quantity for t in open_positions)
        unrealized_pnl = sum(
            (self._get_current_price(t.symbol) - t.entry_price) * t.quantity
            for t in open_positions
        )

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": total_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": round(profit_factor, 2),
            "daily_pnl": self.daily_pnl,
            "open_positions": len(open_positions),
            "total_invested": total_invested,
            "unrealized_pnl": unrealized_pnl,
        }

    def _get_current_price(self, symbol: str) -> float:
        return 0.0

    def reset_daily(self):
        self.daily_pnl = 0.0

    def get_portfolio_summary(self) -> str:
        metrics = self.calculate_portfolio_metrics()
        open_positions = self.get_open_positions()

        summary = []
        summary.append("=" * 50)
        summary.append("PORTFOLIO SUMMARY")
        summary.append("=" * 50)
        summary.append(f"Capital: Rp {self.capital:,.0f}")
        summary.append(f"Open Positions: {metrics['open_positions']}")
        summary.append(f"Total Invested: Rp {metrics['total_invested']:,.0f}")
        summary.append("")
        summary.append("Performance:")
        summary.append(f"  Total Trades: {metrics['total_trades']}")
        summary.append(f"  Win Rate: {metrics['win_rate']}%")
        summary.append(f"  Total P/L: Rp {metrics['total_pnl']:,.0f}")
        summary.append(f"  Daily P/L: Rp {metrics['daily_pnl']:,.0f}")
        summary.append("=" * 50)

        return "\n".join(summary)
