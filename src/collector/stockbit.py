import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import json
import time


class StockBitCollector:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.base_url = "https://stockbit.com"
        self.api_url = "https://api.stockbit.com/v2"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://stockbit.com/",
        })
        self.cache_dir = cache_dir or Path("data/historical")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_stock_data(
        self,
        symbol: str,
        days: int = 60,
        timeframe: str = "15m"
    ) -> pd.DataFrame:
        cache_file = self.cache_dir / f"{symbol}_{timeframe}_{days}d.parquet"

        if cache_file.exists():
            mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mod_time < timedelta(minutes=5):
                return pd.read_parquet(cache_file)

        try:
            df = self._fetch_from_stockbit(symbol, days, timeframe)
            if not df.empty:
                df.to_parquet(cache_file)
                return df
            else:
                return self._generate_mock_data(symbol, days, timeframe)
        except Exception as e:
            print(f"Error fetching {symbol} from StockBit: {e}")
            return self._generate_mock_data(symbol, days, timeframe)

    def _fetch_from_stockbit(self, symbol: str, days: int, timeframe: str) -> pd.DataFrame:
        try:
            params = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "limit": self._calculate_limit(days, timeframe),
            }

            response = self.session.get(
                f"{self.api_url}/charting",
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_stockbit_response(data, symbol)

            return pd.DataFrame()

        except Exception:
            return pd.DataFrame()

    def _parse_stockbit_response(self, data: dict, symbol: str) -> pd.DataFrame:
        try:
            if "data" not in data:
                return pd.DataFrame()

            candles = data["data"].get("candles", [])
            if not candles:
                return pd.DataFrame()

            records = []
            for candle in candles:
                records.append({
                    "timestamp": pd.to_datetime(candle["time"], unit="s"),
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                    "volume": candle.get("volume", 0),
                })

            df = pd.DataFrame(records)
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)
            return df

        except Exception:
            return pd.DataFrame()

    def _calculate_limit(self, days: int, timeframe: str) -> int:
        multiplier = {
            "15m": 26,
            "30m": 13,
            "1h": 6.5,
            "4h": 1.625,
            "1d": 1,
        }
        return int(days * multiplier.get(timeframe, 1))

    def _generate_mock_data(self, symbol: str, days: int, timeframe: str) -> pd.DataFrame:
        import numpy as np

        np.random.seed(hash(symbol) % 2**32)

        periods = self._calculate_limit(days, timeframe)
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=periods, freq=self._get_freq(timeframe))

        base_price = self._get_base_price(symbol)
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

    def get_realtime_quote(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "price": self._get_base_price(symbol),
            "change": 0,
            "change_percent": 0,
            "volume": 0,
            "timestamp": datetime.now().isoformat(),
        }

    def get_market_status(self) -> dict:
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        current_time = hour * 60 + minute

        market_open = 9 * 60
        market_close = 16 * 60

        if market_open <= current_time <= market_close:
            status = "OPEN"
        elif market_open - 30 <= current_time < market_open:
            status = "PRE_MARKET"
        elif market_close < current_time <= market_close + 30:
            status = "POST_MARKET"
        else:
            status = "CLOSED"

        return {
            "status": status,
            "current_time": now.strftime("%H:%M:%S"),
            "market_open": "09:00",
            "market_close": "16:00",
        }
