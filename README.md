# IDX Intraday Stock Screener

Sistem screening saham Indonesia (IDX) untuk strategi **Beli Pagi, Jual Sore** dengan pendekatan Momentum/Breakout.

## Features

- **Multi-Indicator Screening**: Volume, RSI, MACD, Bollinger Bands, EMA
- **Signal Scoring**: Sistem scoring 0-100 untuk validasi sinyal
- **Risk Management**: Position sizing, Stop Loss, Take Profit
- **Auto Scheduler**: Monitoring otomatis setiap 15 menit
- **Alerts**: CLI, Telegram, Email notifications
- **CLI Interface**: Command line untuk manual screening

## Installation

```bash
cd idx-screener
pip install -r requirements.txt
pip install -e .
```

## Usage

### Manual Screening

```bash
# Screen all stocks in watchlist
py -m src screen

# Screen specific stock
py -m src screen --symbol BBCA

# Analyze single stock
py -m src analyze BBCA

# Show watchlist
py -m src watchlist

# Add to watchlist
py -m src add BBNI

# Remove from watchlist
py -m src remove BBNI
```

### Auto Mode

```bash
# Run auto scheduler
py -m src auto

# Run in background
py -m src auto --background
```

### Other Commands

```bash
# Show market status
py -m src status

# Show risk management info
py -m src risk

# Backtest (coming soon)
py -m src backtest
```

## Configuration

Edit `config/config.yaml` to customize:

- **Indicators**: Threshold dan period untuk setiap indikator
- **Signal Scoring**: Minimum score untuk valid signal
- **Risk Management**: Capital, risk per trade, max positions
- **Alerts**: Telegram bot token, email settings
- **Scheduler**: Interval screening, trading hours

## Indikator

| Indikator | Fungsi | Bobot |
|-----------|--------|-------|
| Volume | Deteksi lonjakan volume | 30% |
| Trend (EMA/ADX) | Deteksi trend | 25% |
| RSI | Overbought/Oversold | 20% |
| MACD | Momentum confirmation | 15% |
| Bollinger | Volatility squeeze | 10% |

## Signal Score

- **80-100**: STRONG signal
- **60-79**: MEDIUM signal
- **40-59**: WEAK signal
- **<40**: NO SIGNAL

## Risk Management

- **Position Sizing**: 2% risk per trade
- **Stop Loss**: ATR-based (1.5x ATR)
- **Take Profit**: Risk:Reward ratio 1:2
- **Max Positions**: 5 stocks

## Tech Stack

- Python 3.10+
- pandas & pandas-ta (Technical Analysis)
- Click (CLI Framework)
- Rich (Terminal Output)
- requests & BeautifulSoup (Web Scraping)
- python-telegram-bot (Telegram Alerts)

## Disclaimer

Tool ini hanya untuk **research dan pendidikan**. Selalu lakukan riset sendiri sebelum trading. Trading saham memiliki risiko tinggi.

## License

MIT
