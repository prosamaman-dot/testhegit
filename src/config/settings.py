"""
Centralized configuration for the scalp bot.

Adjust values via environment variables or edit defaults below.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Exchange: "binance", "mexc", "okx", or "bybit"
    exchange: str = os.getenv("EXCHANGE", "bybit").lower()
    # Trading symbols (comma-separated). Fallback to single `SYMBOL` for backward compatibility
    symbols_csv: str = os.getenv(
        "SYMBOLS",
        os.getenv("SYMBOL", "BTC/USDT,ETH/USDT,SOL/USDT,AVAX/USDT,DOGE/USDT,SHIB/USDT,PEPE/USDT,BONK/USDT,WIF/USDT,ICP/USDT,IMX/USDT,APE/USDT,SUI/USDT,ARB/USDT,OP/USDT,LINK/USDT,UNI/USDT,AAVE/USDT,CRV/USDT,COMP/USDT,MANA/USDT,SAND/USDT,AXS/USDT,ENJ/USDT,CHZ/USDT,FLOW/USDT,NEAR/USDT,ALGO/USDT,ATOM/USDT,DOT/USDT,ADA/USDT,XRP/USDT,LTC/USDT,BCH/USDT,ETC/USDT,TRX/USDT,XLM/USDT,THETA/USDT,FIL/USDT,APT/USDT,SEI/USDT,INJ/USDT,TIA/USDT,PYTH/USDT,JUP/USDT"),
    )
    # Timeframes used
    tf_fast: str = os.getenv("TF_FAST", "15m")  # 15m for entry signals
    tf_slow: str = os.getenv("TF_SLOW", "1h")   # 1h for trend analysis
    tf_medium: str = os.getenv("TF_MEDIUM", "4h")  # 4h for major trend
    # Number of candles to fetch for indicators
    candles_limit: int = int(os.getenv("CANDLES_LIMIT", "300"))
    # Min seconds between loops
    loop_interval_sec: float = float(os.getenv("LOOP_INTERVAL_SEC", "300"))  # 5 minutes for swing trading
    # Telegram (env can override these defaults)
    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN") or "8330738447:AAEvV_9K2i-4hfRfR68t6ogpClovhrTcies"
    telegram_chat_id: str | None = os.getenv("TELEGRAM_CHAT_ID") or "6849840329"
    telegram_friend_chat_id: str | None = os.getenv("TELEGRAM_FRIEND_CHAT_ID") or "674144631"
    # Risk - Swing trading (higher targets, wider stops)
    target_rr: float = float(os.getenv("TARGET_RR", "3.0"))  # 3:1 RR for swing trading
    max_sl_pct: float = float(os.getenv("MAX_SL_PCT", "2.0"))  # Wider SL for swing trades
    min_sl_pct: float = float(os.getenv("MIN_SL_PCT", "0.5"))  # Minimum 0.5% SL for swing trades
    atr_window: int = int(os.getenv("ATR_WINDOW", "14"))
    rsi_window: int = int(os.getenv("RSI_WINDOW", "9"))  # More sensitive for scalping
    macd_fast: int = int(os.getenv("MACD_FAST", "12"))
    macd_slow: int = int(os.getenv("MACD_SLOW", "26"))
    macd_signal: int = int(os.getenv("MACD_SIGNAL", "9"))
    # Strategy improvements - Very selective for swing trading
    slow_trend_ema: int = int(os.getenv("SLOW_TREND_EMA", "50"))  # Longer EMA for swing trends
    min_volatility_pct: float = float(os.getenv("MIN_VOLATILITY_PCT", "1.0"))  # High volatility for swing trades
    min_macd_hist_abs: float = float(os.getenv("MIN_MACD_HIST_ABS", "0.01"))  # Strong MACD for swing trades
    # Strategy selection (comma-separated) - More strategies for more signals
    # Available: triple_ema, vwap_fade, bb_squeeze, fast_macd, range_scalp, breakout_retest, 
    #            keltner_stoch, vwap_ema_confluence, volume_spike, heikin_ashi, social_sentiment, original
    active_strategies: str = os.getenv("ACTIVE_STRATEGIES", "triple_ema,breakout_retest")  # Only best swing strategies
    # Triple EMA settings
    ema_fast: int = int(os.getenv("EMA_FAST", "8"))
    ema_medium: int = int(os.getenv("EMA_MEDIUM", "21"))
    ema_slow: int = int(os.getenv("EMA_SLOW", "55"))
    ema_rsi_window: int = int(os.getenv("EMA_RSI_WINDOW", "9"))
    # VWAP settings
    vwap_window: int = int(os.getenv("VWAP_WINDOW", "20"))
    vwap_divergence_pct: float = float(os.getenv("VWAP_DIVERGENCE_PCT", "0.15"))  # 0.15% divergence threshold for more signals
    # Bollinger Bands settings
    bb_window: int = int(os.getenv("BB_WINDOW", "20"))
    bb_std_dev: float = float(os.getenv("BB_STD_DEV", "2.0"))
    bb_squeeze_threshold: float = float(os.getenv("BB_SQUEEZE_THRESHOLD", "0.1"))  # 0.1% band width threshold
    # Fast MACD settings
    fast_macd_fast: int = int(os.getenv("FAST_MACD_FAST", "6"))
    fast_macd_slow: int = int(os.getenv("FAST_MACD_SLOW", "13"))
    fast_macd_signal: int = int(os.getenv("FAST_MACD_SIGNAL", "5"))
    # Keltner Channel settings
    keltner_window: int = int(os.getenv("KELTNER_WINDOW", "20"))
    keltner_atr_mult: float = float(os.getenv("KELTNER_ATR_MULT", "2.0"))
    # Stochastic settings
    stoch_k_period: int = int(os.getenv("STOCH_K_PERIOD", "14"))
    stoch_d_period: int = int(os.getenv("STOCH_D_PERIOD", "3"))
    # Range scalp settings
    range_lookback: int = int(os.getenv("RANGE_LOOKBACK", "30"))  # bars to identify range
    range_bounce_confirm: int = int(os.getenv("RANGE_BOUNCE_CONFIRM", "2"))  # candles for confirmation
    # Execution improvements - Swing trading (longer cooldowns)
    breakeven_trigger_r: float = float(os.getenv("BREAKEVEN_TRIGGER_R", "0.5"))  # Move to breakeven at 50% profit
    cooldown_after_stop_sec: float = float(os.getenv("COOLDOWN_AFTER_STOP_SEC", "3600"))  # 1 hour cooldown after loss
    cooldown_between_signals_sec: float = float(os.getenv("COOLDOWN_BETWEEN_SIGNALS_SEC", "1800"))  # 30 minutes between signals
    # Volume analysis settings
    volume_spike_threshold: float = float(os.getenv("VOLUME_SPIKE_THRESHOLD", "3.0"))  # 3x average volume (more selective)
    volume_lookback_periods: int = int(os.getenv("VOLUME_LOOKBACK_PERIODS", "20"))  # periods to calculate average
    # Breakout detection settings
    breakout_lookback_periods: int = int(os.getenv("BREAKOUT_LOOKBACK_PERIODS", "20"))  # periods for breakout detection
    breakout_confirmation_candles: int = int(os.getenv("BREAKOUT_CONFIRMATION_CANDLES", "3"))  # candles to confirm breakout
    # Heikin Ashi settings
    heikin_ashi_trend_periods: int = int(os.getenv("HEIKIN_ASHI_TREND_PERIODS", "8"))  # periods for trend confirmation (more selective)
    # Social sentiment settings
    sentiment_enabled: bool = os.getenv("SENTIMENT_ENABLED", "1") == "1"
    sentiment_threshold: float = float(os.getenv("SENTIMENT_THRESHOLD", "0.6"))  # 0.6 = 60% positive sentiment
    # News feed settings
    news_enabled: bool = os.getenv("NEWS_ENABLED", "1") == "1"
    news_check_interval: int = int(os.getenv("NEWS_CHECK_INTERVAL", "1800"))  # 30 minutes
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")
    log_to_file: bool = os.getenv("LOG_TO_FILE", "1") == "1"
    log_file_path: str = os.getenv("LOG_FILE", "bot.log")


settings = Settings()

# Convenience accessor returning a clean list of symbols
def get_symbols() -> list[str]:
    return [s.strip() for s in settings.symbols_csv.split(',') if s.strip()]


