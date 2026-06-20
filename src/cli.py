import click
from rich.console import Console
from datetime import datetime

from .config import load_config, load_watchlist, save_watchlist, AppConfig
from .collector import StockBitCollector
from .screener import MultiIndicatorScreener
from .alerts import CLIAlert
from .risk import PositionSizer, PortfolioManager
from .scheduler import AutoScheduler


console = Console()


@click.group()
@click.version_option(version="1.0.0")
def main():
    """IDX Intraday Stock Screener - Beli Pagi Jual Sore"""
    pass


@main.command()
@click.option("--symbol", "-s", help="Stock symbol to screen")
@click.option("--strict", is_flag=True, help="Strict screening with multi-indicator")
@click.option("--days", "-d", default=60, help="Days of historical data")
@click.option("--timeframe", "-t", default="15m", help="Timeframe (15m, 30m, 1h)")
def screen(symbol, strict, days, timeframe):
    """Screen stocks for trading signals"""
    config = load_config()
    collector = StockBitCollector()
    screener = MultiIndicatorScreener(config)
    cli_alert = CLIAlert()

    cli_alert.show_market_status(collector.get_market_status())

    if symbol:
        symbols = [symbol.upper()]
    else:
        symbols = load_watchlist()

    if not symbols:
        cli_alert.show_error("No symbols in watchlist")
        return

    cli_alert.show_info(f"Screening {len(symbols)} stocks...")

    stocks_data = {}
    for sym in symbols:
        df = collector.get_stock_data(sym, days=days, timeframe=timeframe)
        if not df.empty:
            stocks_data[sym] = df

    signals = screener.screen_multiple(stocks_data)
    cli_alert.show_signals(signals)


@main.command()
@click.argument("symbol")
@click.option("--days", "-d", default=60, help="Days of historical data")
def analyze(symbol, days):
    """Analyze a single stock"""
    config = load_config()
    collector = StockBitCollector()
    screener = MultiIndicatorScreener(config)
    cli_alert = CLIAlert()

    symbol = symbol.upper()
    cli_alert.show_info(f"Analyzing {symbol}...")

    df = collector.get_stock_data(symbol, days=days, timeframe="15m")

    if df.empty:
        cli_alert.show_error(f"No data found for {symbol}")
        return

    from .data_models import StockData
    stock_data = StockData.from_dataframe(symbol, df)
    analysis = screener.analyze_stock(stock_data)

    cli_alert.console.print(f"\n[bold cyan]Analysis for {symbol}[/bold cyan]\n")
    cli_alert.console.print(f"Last Price: Rp {analysis['last_price']:,.0f}")
    cli_alert.console.print(f"Change: {analysis['change_percent']}%")

    indicators = analysis["indicators"]
    cli_alert.console.print(f"\n[bold]Indicators:[/bold]")
    cli_alert.console.print(f"  Volume Ratio: {indicators.get('volume_ratio', 0):.1f}x")
    cli_alert.console.print(f"  RSI: {indicators.get('rsi', 0):.0f}")
    cli_alert.console.print(f"  MACD: {'Bullish' if indicators.get('bullish', False) else 'Bearish'}")
    cli_alert.console.print(f"  Trend: {indicators.get('trend', 'unknown')}")
    cli_alert.console.print(f"  Bollinger: {indicators.get('position', 'unknown')}")

    signal = analysis["signal"]
    cli_alert.console.print(f"\n[bold]Signal:[/bold]")
    cli_alert.console.print(f"  Score: {signal['total_score']}/100")
    cli_alert.console.print(f"  Strength: {signal['strength']}")
    cli_alert.console.print(f"  Valid: {'Yes' if signal['is_valid'] else 'No'}")


@main.command()
@click.option("--background", "-b", is_flag=True, help="Run in background")
def auto(background):
    """Run auto screening scheduler"""
    scheduler = AutoScheduler()

    if background:
        import threading
        thread = threading.Thread(target=scheduler.start, daemon=True)
        thread.start()
        console.print("[green]Scheduler started in background[/green]")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
    else:
        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.stop()


@main.command()
def watchlist():
    """Show current watchlist"""
    symbols = load_watchlist()
    cli_alert = CLIAlert()

    if not symbols:
        cli_alert.show_info("Watchlist is empty")
        return

    cli_alert.console.print(f"\n[bold cyan]Watchlist ({len(symbols)} stocks)[/bold cyan]\n")
    for i, symbol in enumerate(symbols, 1):
        cli_alert.console.print(f"  {i}. {symbol}")


@main.command()
@click.argument("symbol")
def add(symbol):
    """Add stock to watchlist"""
    symbol = symbol.upper()
    symbols = load_watchlist()

    if symbol in symbols:
        console.print(f"[yellow]{symbol} already in watchlist[/yellow]")
        return

    symbols.append(symbol)
    save_watchlist(symbols)
    console.print(f"[green]{symbol} added to watchlist[/green]")


@main.command()
@click.argument("symbol")
def remove(symbol):
    """Remove stock from watchlist"""
    symbol = symbol.upper()
    symbols = load_watchlist()

    if symbol not in symbols:
        console.print(f"[yellow]{symbol} not in watchlist[/yellow]")
        return

    symbols.remove(symbol)
    save_watchlist(symbols)
    console.print(f"[green]{symbol} removed from watchlist[/green]")


@main.command()
def risk():
    """Show risk management info"""
    config = load_config()
    position_sizer = PositionSizer(config)
    cli_alert = CLIAlert()

    summary = position_sizer.get_risk_summary()

    cli_alert.console.print("\n[bold cyan]Risk Management[/bold cyan]\n")
    cli_alert.console.print(f"  Capital: Rp {summary['capital']:,.0f}")
    cli_alert.console.print(f"  Risk per Trade: {summary['risk_per_trade']*100}%")
    cli_alert.console.print(f"  Max Risk Amount: Rp {summary['max_risk_amount']:,.0f}")
    cli_alert.console.print(f"  Max Positions: {summary['max_positions']}")
    cli_alert.console.print(f"  Max Daily Loss: {summary['max_daily_loss']*100}%")
    cli_alert.console.print(f"  Max Daily Loss Amount: Rp {summary['max_daily_loss_amount']:,.0f}")


@main.command()
@click.option("--days", "-d", default=30, help="Days to backtest")
@click.option("--capital", "-c", default=100000000, help="Initial capital")
def backtest(days, capital):
    """Run backtest (coming soon)"""
    console.print("[yellow]Backtest feature coming soon![/yellow]")


@main.command()
def status():
    """Show market status"""
    collector = StockBitCollector()
    cli_alert = CLIAlert()

    status = collector.get_market_status()
    cli_alert.show_market_status(status)


def main_entry():
    main()


if __name__ == "__main__":
    main()
