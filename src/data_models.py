from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import pandas as pd


@dataclass
class OHLCV:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass
class StockData:
    symbol: str
    data: pd.DataFrame
    last_price: float = 0.0
    last_volume: int = 0
    change_percent: float = 0.0

    @classmethod
    def from_dataframe(cls, symbol: str, df: pd.DataFrame) -> "StockData":
        if df.empty:
            return cls(symbol=symbol, data=df)

        last_row = df.iloc[-1]
        prev_close = df.iloc[-2]["close"] if len(df) > 1 else last_row["close"]
        change = ((last_row["close"] - prev_close) / prev_close) * 100 if prev_close > 0 else 0

        return cls(
            symbol=symbol,
            data=df,
            last_price=last_row["close"],
            last_volume=int(last_row["volume"]),
            change_percent=round(change, 2),
        )


@dataclass
class Signal:
    symbol: str
    signal_type: str
    score: int
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    indicators: dict
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "score": self.score,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "timestamp": self.timestamp.isoformat(),
            "indicators": self.indicators,
            "message": self.message,
        }


@dataclass
class TradeResult:
    symbol: str
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    quantity: int = 0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    status: str = "open"

    def close(self, exit_date: datetime, exit_price: float):
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.pnl = (exit_price - self.entry_price) * self.quantity
        self.pnl_percent = ((exit_price - self.entry_price) / self.entry_price) * 100
        self.status = "closed"


@dataclass
class BacktestMetrics:
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_return: float = 0.0
    avg_return: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
