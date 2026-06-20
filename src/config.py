import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


CONFIG_DIR = Path(__file__).parent.parent / "config"
DATA_DIR = Path(__file__).parent.parent / "data"
LOGS_DIR = Path(__file__).parent.parent / "logs"


@dataclass
class VolumeConfig:
    spike_threshold: float = 2.0
    lookback_period: int = 20


@dataclass
class TrendConfig:
    ema_fast: int = 9
    ema_slow: int = 21
    adx_threshold: int = 25


@dataclass
class MomentumConfig:
    rsi_period: int = 14
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9


@dataclass
class VolatilityConfig:
    bb_period: int = 20
    bb_std: float = 2.0
    atr_period: int = 14


@dataclass
class IndicatorsConfig:
    volume: VolumeConfig = field(default_factory=VolumeConfig)
    trend: TrendConfig = field(default_factory=TrendConfig)
    momentum: MomentumConfig = field(default_factory=MomentumConfig)
    volatility: VolatilityConfig = field(default_factory=VolatilityConfig)


@dataclass
class SignalScoringConfig:
    min_score: int = 70
    weights: dict = field(default_factory=lambda: {
        "volume": 30,
        "trend": 25,
        "rsi": 20,
        "macd": 15,
        "bollinger": 10
    })


@dataclass
class StopLossConfig:
    method: str = "atr"
    atr_multiplier: float = 1.5


@dataclass
class TakeProfitConfig:
    method: str = "risk_reward"
    ratio: float = 2.0


@dataclass
class RiskManagementConfig:
    capital: float = 100000000
    risk_per_trade: float = 0.02
    max_positions: int = 5
    max_daily_loss: float = 0.05
    stop_loss: StopLossConfig = field(default_factory=StopLossConfig)
    take_profit: TakeProfitConfig = field(default_factory=TakeProfitConfig)


@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


@dataclass
class EmailConfig:
    enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender: str = ""
    password: str = ""
    receiver: str = ""


@dataclass
class AlertsConfig:
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    real_time: bool = True
    daily_summary: bool = True
    summary_time: str = "16:05"


@dataclass
class SchedulerConfig:
    mode: str = "hybrid"
    interval_minutes: int = 15
    trading_hours_start: str = "09:00"
    trading_hours_end: str = "16:00"


@dataclass
class GLMConfig:
    api_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    model: str = "GLM-5.1"
    temperature: float = 0.3
    max_tokens: int = 1024


@dataclass
class IntradayConfig:
    enabled: bool = True
    morning_start: str = "09:00"
    morning_end: str = "12:00"
    afternoon_start: str = "13:00"
    afternoon_end: str = "15:30"
    interval_minutes: int = 15
    min_confidence: int = 60
    group_chat_id: str = ""
    send_summary: bool = True
    summary_time: str = "16:05"


@dataclass
class AppConfig:
    indicators: IndicatorsConfig = field(default_factory=IndicatorsConfig)
    signal_scoring: SignalScoringConfig = field(default_factory=SignalScoringConfig)
    risk_management: RiskManagementConfig = field(default_factory=RiskManagementConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    glm: GLMConfig = field(default_factory=GLMConfig)
    intraday: IntradayConfig = field(default_factory=IntradayConfig)
    watchlist: list = field(default_factory=list)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    if config_path is None:
        config_path = CONFIG_DIR / "config.yaml"

    if not config_path.exists():
        return AppConfig()

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    config = AppConfig()

    if "indicators" in data:
        ind = data["indicators"]
        if "volume" in ind:
            config.indicators.volume = VolumeConfig(**ind["volume"])
        if "trend" in ind:
            config.indicators.trend = TrendConfig(**ind["trend"])
        if "momentum" in ind:
            config.indicators.momentum = MomentumConfig(**ind["momentum"])
        if "volatility" in ind:
            config.indicators.volatility = VolatilityConfig(**ind["volatility"])

    if "signal_scoring" in data:
        ss = data["signal_scoring"]
        config.signal_scoring.min_score = ss.get("min_score", 70)
        config.signal_scoring.weights = ss.get("weights", config.signal_scoring.weights)

    if "risk_management" in data:
        rm = data["risk_management"]
        config.risk_management.capital = rm.get("capital", 100000000)
        config.risk_management.risk_per_trade = rm.get("risk_per_trade", 0.02)
        config.risk_management.max_positions = rm.get("max_positions", 5)
        config.risk_management.max_daily_loss = rm.get("max_daily_loss", 0.05)
        if "stop_loss" in rm:
            config.risk_management.stop_loss = StopLossConfig(**rm["stop_loss"])
        if "take_profit" in rm:
            config.risk_management.take_profit = TakeProfitConfig(**rm["take_profit"])

    if "alerts" in data:
        al = data["alerts"]
        if "telegram" in al:
            config.alerts.telegram = TelegramConfig(**al["telegram"])
        if "email" in al:
            config.alerts.email = EmailConfig(**al["email"])
        config.alerts.real_time = al.get("real_time", True)
        config.alerts.daily_summary = al.get("daily_summary", True)
        config.alerts.summary_time = al.get("summary_time", "16:05")

    if "scheduler" in data:
        sc = data["scheduler"]
        config.scheduler.mode = sc.get("mode", "hybrid")
        config.scheduler.interval_minutes = sc.get("interval_minutes", 15)
        hours = sc.get("trading_hours", {})
        config.scheduler.trading_hours_start = hours.get("start", "09:00")
        config.scheduler.trading_hours_end = hours.get("end", "16:00")

    if "glm" in data:
        gl = data["glm"]
        config.glm.api_url = gl.get("api_url", config.glm.api_url)
        config.glm.model = gl.get("model", config.glm.model)
        config.glm.temperature = gl.get("temperature", config.glm.temperature)
        config.glm.max_tokens = gl.get("max_tokens", config.glm.max_tokens)

    if "intraday" in data:
        it = data["intraday"]
        config.intraday.enabled = it.get("enabled", True)
        config.intraday.morning_start = it.get("morning_start", "09:00")
        config.intraday.morning_end = it.get("morning_end", "12:00")
        config.intraday.afternoon_start = it.get("afternoon_start", "13:00")
        config.intraday.afternoon_end = it.get("afternoon_end", "15:30")
        config.intraday.interval_minutes = it.get("interval_minutes", 15)
        config.intraday.min_confidence = it.get("min_confidence", 60)
        config.intraday.group_chat_id = it.get("group_chat_id", "")
        config.intraday.send_summary = it.get("send_summary", True)
        config.intraday.summary_time = it.get("summary_time", "16:05")

    if "watchlist" in data:
        config.watchlist = data["watchlist"]

    return config


def load_watchlist() -> list:
    watchlist_path = CONFIG_DIR / "watchlist.yaml"
    if not watchlist_path.exists():
        return []

    with open(watchlist_path, "r") as f:
        data = yaml.safe_load(f)

    return data.get("watchlist", [])


def save_watchlist(watchlist: list):
    watchlist_path = CONFIG_DIR / "watchlist.yaml"
    with open(watchlist_path, "w") as f:
        yaml.dump({"watchlist": watchlist}, f, default_flow_style=False)
