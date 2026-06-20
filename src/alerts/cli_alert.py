from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from typing import List
from datetime import datetime

from ..data_models import Signal


class CLIAlert:
    def __init__(self):
        self.console = Console()

    def show_signal(self, signal: Signal):
        color = "green" if signal.signal_type == "BUY" else "red"

        title = Text(f"🔔 {signal.signal_type} SIGNAL - {signal.symbol}", style=f"bold {color}")

        content = []
        content.append(f"💰 Entry: Rp {signal.entry_price:,.0f}")
        content.append(f"🛑 Stop Loss: Rp {signal.stop_loss:,.0f}")
        content.append(f"🎯 Take Profit: Rp {signal.take_profit:,.0f}")
        content.append(f"📊 Score: {signal.score}/100")
        content.append("")

        content.append("Indikator:")
        indicators = signal.indicators

        volume_ratio = indicators.get("volume_ratio", 0)
        if volume_ratio >= 2.0:
            content.append(f"  ✅ Volume: {volume_ratio:.1f}x average")
        else:
            content.append(f"  ⚠️ Volume: {volume_ratio:.1f}x average")

        rsi = indicators.get("rsi", 50)
        if 30 < rsi < 70:
            content.append(f"  ✅ RSI: {rsi:.0f} (Neutral)")
        elif rsi <= 30:
            content.append(f"  ✅ RSI: {rsi:.0f} (Oversold)")
        else:
            content.append(f"  ⚠️ RSI: {rsi:.0f} (Overbought)")

        macd_bullish = indicators.get("macd_bullish", False)
        if macd_bullish:
            content.append("  ✅ MACD: Bullish")
        else:
            content.append("  ⚠️ MACD: Bearish")

        trend = indicators.get("trend", "unknown")
        if "uptrend" in trend.lower():
            content.append(f"  ✅ Trend: {trend}")
        else:
            content.append(f"  ⚠️ Trend: {trend}")

        bb_position = indicators.get("bb_position", "unknown")
        content.append(f"  📈 Bollinger: {bb_position}")

        content.append("")
        content.append(f"⏰ {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        panel = Panel(
            "\n".join(content),
            title=title,
            border_style=color,
            box=box.DOUBLE,
        )

        self.console.print(panel)

    def show_signals(self, signals: List[Signal]):
        if not signals:
            self.console.print("[yellow]No signals found[/yellow]")
            return

        self.console.print(f"\n[bold cyan]📊 Found {len(signals)} signal(s)[/bold cyan]\n")

        for signal in signals:
            self.show_signal(signal)
            self.console.print()

    def show_summary(self, signals: List[Signal], date: datetime = None):
        if date is None:
            date = datetime.now()

        total = len(signals)
        buy_signals = [s for s in signals if s.signal_type == "BUY"]
        strong_signals = [s for s in signals if s.score >= 80]
        medium_signals = [s for s in signals if 60 <= s.score < 80]

        table = Table(title=f"📊 Daily Summary - {date.strftime('%Y-%m-%d')}", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Signals", str(total))
        table.add_row("BUY Signals", str(len(buy_signals)))
        table.add_row("Strong Signals", str(len(strong_signals)))
        table.add_row("Medium Signals", str(len(medium_signals)))

        if strong_signals:
            table.add_row("Top Signal", f"{strong_signals[0].symbol} ({strong_signals[0].score})")

        self.console.print(table)

        if signals:
            self.console.print("\n[bold]Top Signals:[/bold]")
            for signal in signals[:5]:
                color = "green" if signal.score >= 80 else "yellow" if signal.score >= 60 else "red"
                self.console.print(
                    f"  [{color}]{signal.symbol}[/{color}] - "
                    f"Score: {signal.score}, "
                    f"Entry: Rp {signal.entry_price:,.0f}"
                )

    def show_market_status(self, status: dict):
        status_color = "green" if status["status"] == "OPEN" else "yellow" if status["status"] in ["PRE_MARKET", "POST_MARKET"] else "red"

        table = Table(title="📈 Market Status", box=box.ROUNDED)
        table.add_column("Info", style="cyan")
        table.add_column("Value")

        table.add_row("Status", f"[{status_color}]{status['status']}[/{status_color}]")
        table.add_row("Current Time", status["current_time"])
        table.add_row("Market Open", status["market_open"])
        table.add_row("Market Close", status["market_close"])

        self.console.print(table)

    def show_error(self, message: str):
        self.console.print(f"[bold red]❌ Error: {message}[/bold red]")

    def show_success(self, message: str):
        self.console.print(f"[bold green]✅ {message}[/bold green]")

    def show_info(self, message: str):
        self.console.print(f"[bold blue]ℹ️ {message}[/bold blue]")
