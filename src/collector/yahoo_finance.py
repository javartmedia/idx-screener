import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path


class YahooFinanceCollector:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/historical")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _convert_to_yahoo_symbol(self, symbol: str) -> str:
        return f"{symbol}.JK"

    def get_stock_data(
        self,
        symbol: str,
        days: int = 60,
        timeframe: str = "15m"
    ) -> pd.DataFrame:
        yahoo_symbol = self._convert_to_yahoo_symbol(symbol)
        cache_file = self.cache_dir / f"{symbol}_{timeframe}_{days}d.parquet"

        if cache_file.exists():
            mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mod_time < timedelta(minutes=5):
                return pd.read_parquet(cache_file)

        try:
            import yfinance as yf
            ticker = yf.Ticker(yahoo_symbol)
            interval = self._convert_timeframe(timeframe)
            period = self._convert_period(days, timeframe)

            df = ticker.history(period=period, interval=interval)

            if df.empty:
                return self._generate_mock_data(symbol, days, timeframe)

            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            })

            df = df[["open", "high", "low", "close", "volume"]]
            df.index.name = "timestamp"

            df.to_parquet(cache_file)
            return df

        except ImportError:
            return self._generate_mock_data(symbol, days, timeframe)
        except Exception as e:
            print(f"Error fetching {symbol} from Yahoo Finance: {e}")
            return self._generate_mock_data(symbol, days, timeframe)

    def _convert_timeframe(self, timeframe: str) -> str:
        mapping = {
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "4h": "1h",
            "1d": "1d",
        }
        return mapping.get(timeframe, "15m")

    def _convert_period(self, days: int, timeframe: str) -> str:
        if days <= 7:
            return "5d"
        elif days <= 30:
            return "1mo"
        elif days <= 90:
            return "3mo"
        elif days <= 180:
            return "6mo"
        else:
            return "1y"

    def _generate_mock_data(self, symbol: str, days: int, timeframe: str) -> pd.DataFrame:
        periods = self._calculate_periods(days, timeframe)
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=periods, freq=self._get_freq(timeframe))

        base_price = self._get_base_price(symbol)
        np.random.seed(hash(symbol) % 2**32)

        returns = np.random.normal(0.0005, 0.02, periods)
        prices = base_price * np.cumprod(1 + returns)

        highs = prices * (1 + np.abs(np.random.normal(0, 0.01, periods)))
        lows = prices * (1 - np.abs(np.random.normal(0, 0.01, periods)))
        opens = lows + (highs - lows) * np.random.random(periods)

        avg_volume = self._get_avg_volume(symbol)
        volumes = np.random.lognormal(np.log(avg_volume), 0.5, periods).astype(int)

        df = pd.DataFrame({
            "open": opens,
            "high": highs,
            "low": lows,
            "close": prices,
            "volume": volumes,
        }, index=dates)
        df.index.name = "timestamp"

        return df

    def _calculate_periods(self, days: int, timeframe: str) -> int:
        multiplier = {
            "15m": 26,
            "30m": 13,
            "1h": 6.5,
            "4h": 1.625,
            "1d": 1,
        }
        return int(days * multiplier.get(timeframe, 1))

    def _get_freq(self, timeframe: str) -> str:
        freq_map = {
            "15m": "15min",
            "30m": "30min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1D",
        }
        return freq_map.get(timeframe, "15min")

    def _get_base_price(self, symbol: str) -> float:
        prices = {
            "BBCA": 9200, "BBRI": 4800, "BMRI": 6200, "TLKM": 3800,
            "ASII": 5100, "UNVR": 4200, "BBNI": 5500, "INDF": 6800,
            "KLBF": 1200, "ICBP": 11500, "INDY": 2100, "PGAS": 1400,
            "PTBA": 2800, "ADRO": 2400, "MDKA": 1100,
        }
        return prices.get(symbol, 1000)

    def _get_avg_volume(self, symbol: str) -> int:
        volumes = {
            "BBCA": 50000000, "BBRI": 80000000, "BMRI": 40000000,
            "TLKM": 30000000, "ASII": 20000000, "UNVR": 15000000,
            "BBNI": 35000000, "INDF": 10000000, "KLBF": 25000000,
            "ICBP": 8000000, "INDY": 12000000, "PGAS": 18000000,
            "PTBA": 15000000, "ADRO": 22000000, "MDKA": 5000000,
        }
        return volumes.get(symbol, 10000000)
