from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import math
import asyncio

from src.config.settings import settings
from src.utils.simple_logger import create_logger
from src.strategies.volume_strategies import generate_volume_signal
from src.strategies.sentiment_analysis import get_sentiment_signal


logger = create_logger(__name__)


def _sma(values: List[float], window: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    acc = 0.0
    q: List[float] = []
    for v in values:
        q.append(v)
        acc += v
        if len(q) > window:
            acc -= q.pop(0)
        out.append(acc / window if len(q) == window else None)
    return out


def _ema(values: List[float], window: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    k = 2.0 / (window + 1.0)
    ema_val: Optional[float] = None
    for v in values:
        ema_val = v if ema_val is None else (v - ema_val) * k + ema_val
        out.append(ema_val)
    return out


def rsi(closes: List[float], window: int) -> List[Optional[float]]:
    if len(closes) < window + 1:
        return [None] * len(closes)
    gains: List[float] = [0.0]
    losses: List[float] = [0.0]
    for i in range(1, len(closes)):
        chg = closes[i] - closes[i - 1]
        gains.append(max(chg, 0.0))
        losses.append(max(-chg, 0.0))
    avg_gain = _ema(gains, window)
    avg_loss = _ema(losses, window)
    out: List[Optional[float]] = []
    for g, l in zip(avg_gain, avg_loss):
        if g is None or l is None or l == 0:
            out.append(None)
        else:
            rs = g / l if l != 0 else float("inf")
            out.append(100.0 - 100.0 / (1.0 + rs))
    return out


def macd(closes: List[float], fast: int, slow: int, signal: int) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    macd_line: List[Optional[float]] = []
    for f, s in zip(ema_fast, ema_slow):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)
    signal_line = _ema([v if v is not None else 0.0 for v in macd_line], signal)
    hist: List[Optional[float]] = []
    for m, sig in zip(macd_line, signal_line):
        if m is None or sig is None:
            hist.append(None)
        else:
            hist.append(m - sig)
    return macd_line, signal_line, hist


def true_range(highs: List[float], lows: List[float], closes: List[float]) -> List[float]:
    trs: List[float] = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    return trs


def atr(highs: List[float], lows: List[float], closes: List[float], window: int) -> List[Optional[float]]:
    trs = true_range(highs, lows, closes)
    return _ema(trs, window)


def micro_levels(closes: List[float], window: int = 10) -> Tuple[Optional[float], Optional[float]]:
    if len(closes) < window:
        return None, None
    recent = closes[-window:]
    return min(recent), max(recent)


@dataclass
class Signal:
    side: str  # "LONG" or "SHORT"
    entry: float
    context: Dict[str, float]


def bollinger_bands(closes: List[float], window: int, std_dev: float) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Calculate Bollinger Bands: upper, middle (SMA), lower"""
    if len(closes) < window:
        return [None] * len(closes), [None] * len(closes), [None] * len(closes)
    
    sma_vals = _sma(closes, window)
    upper_band = []
    lower_band = []
    
    for i, sma in enumerate(sma_vals):
        if sma is None or i < window - 1:
            upper_band.append(None)
            lower_band.append(None)
        else:
            # Calculate standard deviation for the window
            window_closes = closes[i - window + 1:i + 1]
            variance = sum((x - sma) ** 2 for x in window_closes) / window
            std = variance ** 0.5
            upper_band.append(sma + std_dev * std)
            lower_band.append(sma - std_dev * std)
    
    return upper_band, sma_vals, lower_band


def vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float], window: int) -> List[Optional[float]]:
    """Calculate Volume Weighted Average Price"""
    if len(highs) < window or len(volumes) < window:
        return [None] * len(closes)
    
    vwap_vals = []
    for i in range(len(closes)):
        if i < window - 1:
            vwap_vals.append(None)
        else:
            # Typical price = (H + L + C) / 3
            typical_prices = [(highs[j] + lows[j] + closes[j]) / 3 for j in range(i - window + 1, i + 1)]
            window_volumes = volumes[i - window + 1:i + 1]
            
            total_volume = sum(window_volumes)
            if total_volume == 0:
                vwap_vals.append(None)
            else:
                vwap = sum(tp * vol for tp, vol in zip(typical_prices, window_volumes)) / total_volume
                vwap_vals.append(vwap)
    
    return vwap_vals


def triple_ema_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Triple EMA trend/pullback strategy"""
    if len(ohlcv_fast) < 60:
        return None
    
    closes = [c[4] for c in ohlcv_fast]
    highs = [c[2] for c in ohlcv_fast]
    lows = [c[3] for c in ohlcv_fast]
    
    # Calculate 3 EMAs
    ema_fast = _ema(closes, settings.ema_fast)
    ema_medium = _ema(closes, settings.ema_medium)
    ema_slow = _ema(closes, settings.ema_slow)
    
    # RSI for momentum filter
    rsi_vals = rsi(closes, settings.ema_rsi_window)
    
    if len(ema_fast) < 3 or len(rsi_vals) < 3:
        return None
    
    last_close = closes[-1]
    last_ema_fast = ema_fast[-1]
    last_ema_medium = ema_medium[-1]
    last_ema_slow = ema_slow[-1]
    last_rsi = rsi_vals[-1]
    
    if any(x is None for x in [last_ema_fast, last_ema_medium, last_ema_slow, last_rsi]):
        return None
    
    # Check for EMA ribbon alignment (trend direction)
    bullish_ribbon = last_ema_fast > last_ema_medium > last_ema_slow
    bearish_ribbon = last_ema_fast < last_ema_medium < last_ema_slow
    
    # Look for pullback to fast EMA and recovery
    prev_close = closes[-2]
    prev_ema_fast = ema_fast[-2]
    
    if prev_ema_fast is None:
        return None
    
    # Long setup: bullish ribbon + pullback to EMA + recovery above EMA + RSI not extreme
    if bullish_ribbon and prev_close <= prev_ema_fast and last_close > last_ema_fast and 30 < last_rsi < 70:
        return Signal("LONG", last_close, {
            "strategy": "triple_ema",
            "ema_fast": float(last_ema_fast),
            "ema_medium": float(last_ema_medium),
            "ema_slow": float(last_ema_slow),
            "rsi": float(last_rsi),
        })
    
    # Short setup: bearish ribbon + pullback to EMA + recovery below EMA + RSI not extreme
    if bearish_ribbon and prev_close >= prev_ema_fast and last_close < last_ema_fast and 30 < last_rsi < 70:
        return Signal("SHORT", last_close, {
            "strategy": "triple_ema",
            "ema_fast": float(last_ema_fast),
            "ema_medium": float(last_ema_medium),
            "ema_slow": float(last_ema_slow),
            "rsi": float(last_rsi),
        })
    
    return None


def vwap_fade_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """VWAP mean-reversion strategy"""
    if len(ohlcv_fast) < settings.vwap_window + 10:
        return None
    
    closes = [c[4] for c in ohlcv_fast]
    highs = [c[2] for c in ohlcv_fast]
    lows = [c[3] for c in ohlcv_fast]
    volumes = [c[5] for c in ohlcv_fast]  # Assuming volume is in position 5
    
    vwap_vals = vwap(highs, lows, closes, volumes, settings.vwap_window)
    
    if len(vwap_vals) < 3:
        return None
    
    last_close = closes[-1]
    last_vwap = vwap_vals[-1]
    prev_close = closes[-2]
    prev_vwap = vwap_vals[-2]
    
    if any(x is None for x in [last_vwap, prev_vwap]):
        return None
    
    # Calculate divergence from VWAP
    divergence_pct = abs(last_close - last_vwap) / last_vwap * 100
    
    # Look for rejection candle (long upper shadow for short, long lower shadow for long)
    current_high = highs[-1]
    current_low = lows[-1]
    current_open = closes[-2] if len(closes) > 1 else closes[-1]
    
    upper_shadow = current_high - max(last_close, current_open)
    lower_shadow = min(last_close, current_open) - current_low
    body_size = abs(last_close - current_open)
    
    # Long setup: price below VWAP + significant divergence + rejection candle with long lower shadow
    if (last_close < last_vwap and 
        divergence_pct > settings.vwap_divergence_pct and 
        lower_shadow > body_size * 1.5 and
        last_close > prev_close):  # Some recovery
        
        return Signal("LONG", last_close, {
            "strategy": "vwap_fade",
            "vwap": float(last_vwap),
            "divergence_pct": float(divergence_pct),
            "lower_shadow": float(lower_shadow),
        })
    
    # Short setup: price above VWAP + significant divergence + rejection candle with long upper shadow
    if (last_close > last_vwap and 
        divergence_pct > settings.vwap_divergence_pct and 
        upper_shadow > body_size * 1.5 and
        last_close < prev_close):  # Some rejection
        
        return Signal("SHORT", last_close, {
            "strategy": "vwap_fade",
            "vwap": float(last_vwap),
            "divergence_pct": float(divergence_pct),
            "upper_shadow": float(upper_shadow),
        })
    
    return None


def bb_squeeze_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Bollinger Band squeeze & bounce strategy"""
    if len(ohlcv_fast) < settings.bb_window + 10:
        return None
    
    closes = [c[4] for c in ohlcv_fast]
    highs = [c[2] for c in ohlcv_fast]
    lows = [c[3] for c in ohlcv_fast]
    
    upper_band, middle_band, lower_band = bollinger_bands(closes, settings.bb_window, settings.bb_std_dev)
    rsi_vals = rsi(closes, settings.rsi_window)
    
    if len(upper_band) < 3 or len(rsi_vals) < 3:
        return None
    
    last_close = closes[-1]
    last_upper = upper_band[-1]
    last_lower = lower_band[-1]
    last_middle = middle_band[-1]
    last_rsi = rsi_vals[-1]
    
    if any(x is None for x in [last_upper, last_lower, last_middle, last_rsi]):
        return None
    
    # Check for squeeze (narrow bands)
    band_width = (last_upper - last_lower) / last_middle * 100
    is_squeeze = band_width < settings.bb_squeeze_threshold
    
    if not is_squeeze:
        return None
    
    # Look for breakout with momentum confirmation
    prev_close = closes[-2]
    prev_upper = upper_band[-2]
    prev_lower = lower_band[-2]
    
    if prev_upper is None or prev_lower is None:
        return None
    
    # Long setup: breakout above upper band + RSI momentum
    if (last_close > last_upper and 
        prev_close <= prev_upper and 
        last_rsi > 50 and 
        last_rsi < 80):  # Not overbought yet
        
        return Signal("LONG", last_close, {
            "strategy": "bb_squeeze",
            "upper_band": float(last_upper),
            "lower_band": float(last_lower),
            "middle_band": float(last_middle),
            "band_width": float(band_width),
            "rsi": float(last_rsi),
        })
    
    # Short setup: breakout below lower band + RSI momentum
    if (last_close < last_lower and 
        prev_close >= prev_lower and 
        last_rsi < 50 and 
        last_rsi > 20):  # Not oversold yet
        
        return Signal("SHORT", last_close, {
            "strategy": "bb_squeeze",
            "upper_band": float(last_upper),
            "lower_band": float(last_lower),
            "middle_band": float(last_middle),
            "band_width": float(band_width),
            "rsi": float(last_rsi),
        })
    
    return None


def fast_macd_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Fast MACD + RSI momentum strategy"""
    if len(ohlcv_fast) < 30:
        return None
    
    closes = [c[4] for c in ohlcv_fast]
    
    # Fast MACD settings
    macd_line, signal_line, hist = macd(closes, settings.fast_macd_fast, settings.fast_macd_slow, settings.fast_macd_signal)
    rsi_vals = rsi(closes, settings.rsi_window)
    
    if len(macd_line) < 3 or len(rsi_vals) < 3:
        return None
    
    last_close = closes[-1]
    last_macd = macd_line[-1]
    last_signal = signal_line[-1]
    last_hist = hist[-1]
    last_rsi = rsi_vals[-1]
    prev_hist = hist[-2]
    
    if any(x is None for x in [last_macd, last_signal, last_hist, last_rsi, prev_hist]):
        return None
    
    # Long setup: MACD cross above signal + histogram flip positive + RSI momentum
    if (last_macd > last_signal and 
        last_hist > 0 and 
        prev_hist <= 0 and  # Histogram flip
        last_rsi > 45 and 
        last_rsi < 75):
        
        return Signal("LONG", last_close, {
            "strategy": "fast_macd",
            "macd": float(last_macd),
            "signal": float(last_signal),
            "histogram": float(last_hist),
            "rsi": float(last_rsi),
        })
    
    # Short setup: MACD cross below signal + histogram flip negative + RSI momentum
    if (last_macd < last_signal and 
        last_hist < 0 and 
        prev_hist >= 0 and  # Histogram flip
        last_rsi < 55 and 
        last_rsi > 25):
        
        return Signal("SHORT", last_close, {
            "strategy": "fast_macd",
            "macd": float(last_macd),
            "signal": float(last_signal),
            "histogram": float(last_hist),
            "rsi": float(last_rsi),
        })
    
    return None


def stochastic(highs: List[float], lows: List[float], closes: List[float], k_period: int, d_period: int) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """Calculate Stochastic oscillator"""
    if len(closes) < k_period:
        return [None] * len(closes), [None] * len(closes)
    
    k_values = []
    for i in range(len(closes)):
        if i < k_period - 1:
            k_values.append(None)
        else:
            period_highs = highs[i - k_period + 1:i + 1]
            period_lows = lows[i - k_period + 1:i + 1]
            highest = max(period_highs)
            lowest = min(period_lows)
            if highest == lowest:
                k_values.append(50.0)
            else:
                k = ((closes[i] - lowest) / (highest - lowest)) * 100.0
                k_values.append(k)
    
    # %D is SMA of %K
    d_values = _sma([k if k is not None else 0.0 for k in k_values], d_period)
    
    return k_values, d_values


def keltner_channels(highs: List[float], lows: List[float], closes: List[float], window: int, atr_mult: float) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Calculate Keltner Channels"""
    ema_vals = _ema(closes, window)
    atr_vals = atr(highs, lows, closes, window)
    
    upper = []
    lower = []
    for e, a in zip(ema_vals, atr_vals):
        if e is None or a is None:
            upper.append(None)
            lower.append(None)
        else:
            upper.append(e + atr_mult * a)
            lower.append(e - atr_mult * a)
    
    return upper, ema_vals, lower


def range_scalp_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Range / support-resistance micro-scalp strategy"""
    if len(ohlcv_fast) < settings.range_lookback + 10:
        return None
    
    closes = [c[4] for c in ohlcv_fast]
    highs = [c[2] for c in ohlcv_fast]
    lows = [c[3] for c in ohlcv_fast]
    volumes = [c[5] for c in ohlcv_fast]
    
    # Identify range from recent bars
    recent_highs = highs[-settings.range_lookback:]
    recent_lows = lows[-settings.range_lookback:]
    
    range_high = max(recent_highs)
    range_low = min(recent_lows)
    range_mid = (range_high + range_low) / 2
    range_size = range_high - range_low
    
    # Only trade if in a defined range (not too wide)
    if range_size / closes[-1] > 0.025:  # More than 2.5% range = trending, not ranging
        return None
    
    last_close = closes[-1]
    last_high = highs[-1]
    last_low = lows[-1]
    
    # Check for rejection candles near support/resistance
    upper_wick = last_high - max(last_close, closes[-2] if len(closes) > 1 else last_close)
    lower_wick = min(last_close, closes[-2] if len(closes) > 1 else last_close) - last_low
    body_size = abs(last_close - (closes[-2] if len(closes) > 1 else last_close))
    
    # Long setup: near support + rejection + volume confirmation
    near_support = last_close < range_low + range_size * 0.2
    bullish_rejection = lower_wick > body_size * 1.5 and last_close > closes[-2] if len(closes) > 1 else False
    
    if near_support and bullish_rejection:
        return Signal("LONG", last_close, {
            "strategy": "range_scalp",
            "range_high": range_high,
            "range_low": range_low,
            "range_mid": range_mid,
        })
    
    # Short setup: near resistance + rejection
    near_resistance = last_close > range_high - range_size * 0.2
    bearish_rejection = upper_wick > body_size * 1.5 and last_close < closes[-2] if len(closes) > 1 else False
    
    if near_resistance and bearish_rejection:
        return Signal("SHORT", last_close, {
            "strategy": "range_scalp",
            "range_high": range_high,
            "range_low": range_low,
            "range_mid": range_mid,
        })
    
    return None


def breakout_retest_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Breakout retest scalp (micro-breakout) strategy"""
    if len(ohlcv_fast) < 20:
        return None
    
    closes = [c[4] for c in ohlcv_fast]
    highs = [c[2] for c in ohlcv_fast]
    lows = [c[3] for c in ohlcv_fast]
    
    # Find recent swing high/low (last 10-15 candles)
    lookback = 15
    recent_highs = highs[-lookback:-2]  # Exclude last 2 candles
    recent_lows = lows[-lookback:-2]
    
    if not recent_highs or not recent_lows:
        return None
    
    swing_high = max(recent_highs)
    swing_low = min(recent_lows)
    
    last_close = closes[-1]
    prev_close = closes[-2]
    prev2_close = closes[-3] if len(closes) > 2 else prev_close
    
    # Bullish breakout retest: broke above swing high, now retesting
    broke_above = prev2_close > swing_high
    retesting = prev_close < swing_high and last_close > swing_high * 0.998  # Near the level
    weak_retest = abs(prev_close - prev2_close) < abs(closes[-3] - closes[-4]) if len(closes) > 3 else True
    
    if broke_above and retesting and weak_retest and last_close > prev_close:
        return Signal("LONG", last_close, {
            "strategy": "breakout_retest",
            "breakout_level": swing_high,
            "swing_low": swing_low,
        })
    
    # Bearish breakout retest: broke below swing low, now retesting
    broke_below = prev2_close < swing_low
    retesting_low = prev_close > swing_low and last_close < swing_low * 1.002
    
    if broke_below and retesting_low and weak_retest and last_close < prev_close:
        return Signal("SHORT", last_close, {
            "strategy": "breakout_retest",
            "breakout_level": swing_low,
            "swing_high": swing_high,
        })
    
    return None


def keltner_stoch_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Keltner Channel + Stochastic scalping strategy"""
    if len(ohlcv_fast) < settings.keltner_window + 20:
        return None
    
    closes = [c[4] for c in ohlcv_fast]
    highs = [c[2] for c in ohlcv_fast]
    lows = [c[3] for c in ohlcv_fast]
    
    upper_kelt, mid_kelt, lower_kelt = keltner_channels(highs, lows, closes, settings.keltner_window, settings.keltner_atr_mult)
    k_vals, d_vals = stochastic(highs, lows, closes, settings.stoch_k_period, settings.stoch_d_period)
    
    if len(upper_kelt) < 3 or len(k_vals) < 3:
        return None
    
    last_close = closes[-1]
    last_upper = upper_kelt[-1]
    last_lower = lower_kelt[-1]
    last_k = k_vals[-1]
    prev_k = k_vals[-2]
    
    if any(x is None for x in [last_upper, last_lower, last_k, prev_k]):
        return None
    
    # Long setup: price touches lower Keltner + stochastic oversold and turning up
    at_lower = last_close <= last_lower * 1.002
    stoch_oversold_turn = last_k < 30 and last_k > prev_k
    
    if at_lower and stoch_oversold_turn:
        return Signal("LONG", last_close, {
            "strategy": "keltner_stoch",
            "keltner_upper": float(last_upper),
            "keltner_lower": float(last_lower),
            "stoch_k": float(last_k),
        })
    
    # Short setup: price touches upper Keltner + stochastic overbought and turning down
    at_upper = last_close >= last_upper * 0.998
    stoch_overbought_turn = last_k > 70 and last_k < prev_k
    
    if at_upper and stoch_overbought_turn:
        return Signal("SHORT", last_close, {
            "strategy": "keltner_stoch",
            "keltner_upper": float(last_upper),
            "keltner_lower": float(last_lower),
            "stoch_k": float(last_k),
        })
    
    return None


def vwap_ema_confluence_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Momentum pullback with VWAP + EMA confluence strategy"""
    if len(ohlcv_fast) < 30:
        return None
    
    closes = [c[4] for c in ohlcv_fast]
    highs = [c[2] for c in ohlcv_fast]
    lows = [c[3] for c in ohlcv_fast]
    volumes = [c[5] for c in ohlcv_fast]
    
    vwap_vals = vwap(highs, lows, closes, volumes, settings.vwap_window)
    ema_vals = _ema(closes, settings.ema_fast)
    
    if len(vwap_vals) < 5 or len(ema_vals) < 5:
        return None
    
    last_close = closes[-1]
    last_vwap = vwap_vals[-1]
    last_ema = ema_vals[-1]
    prev_close = closes[-2]
    
    if any(x is None for x in [last_vwap, last_ema]):
        return None
    
    # Detect momentum burst away from VWAP
    burst_dist = abs(closes[-3] - vwap_vals[-3]) if vwap_vals[-3] else 0
    current_dist = abs(last_close - last_vwap)
    
    # Check if price is pulling back to confluence (VWAP + EMA near each other)
    confluence = abs(last_vwap - last_ema) / last_close < 0.002  # Within 0.2%
    near_confluence = abs(last_close - last_vwap) / last_close < 0.003  # Price near VWAP
    
    # Long setup: was above, pulled back to confluence, resuming up
    if confluence and near_confluence and last_close > prev_close and last_close > last_vwap:
        return Signal("LONG", last_close, {
            "strategy": "vwap_ema_confluence",
            "vwap": float(last_vwap),
            "ema": float(last_ema),
        })
    
    # Short setup: was below, pulled back to confluence, resuming down
    if confluence and near_confluence and last_close < prev_close and last_close < last_vwap:
        return Signal("SHORT", last_close, {
            "strategy": "vwap_ema_confluence",
            "vwap": float(last_vwap),
            "ema": float(last_ema),
        })
    
    return None


def generate_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Main signal generator that tries multiple strategies in order of preference"""
    if len(ohlcv_fast) < 50 or len(ohlcv_slow) < 30:
        return None

    # Get active strategies from config
    active_strategies = [s.strip() for s in settings.active_strategies.split(',') if s.strip()]
    
    # Try each strategy in order until one generates a signal
    for strategy_name in active_strategies:
        signal = None
        
        if strategy_name == "triple_ema":
            signal = triple_ema_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "vwap_fade":
            signal = vwap_fade_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "bb_squeeze":
            signal = bb_squeeze_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "fast_macd":
            signal = fast_macd_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "range_scalp":
            signal = range_scalp_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "breakout_retest":
            signal = breakout_retest_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "keltner_stoch":
            signal = keltner_stoch_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "vwap_ema_confluence":
            signal = vwap_ema_confluence_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "original":
            signal = original_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "volume_spike":
            signal = generate_volume_signal(ohlcv_fast, ohlcv_slow)
        elif strategy_name == "heikin_ashi":
            signal = generate_volume_signal(ohlcv_fast, ohlcv_slow)  # Uses heikin_ashi internally
        elif strategy_name == "social_sentiment":
            # This is async, so we'll handle it separately
            continue
        
        if signal is not None:
            return signal
    
    return None


def original_signal(ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
    """Original strategy for backward compatibility"""
    if len(ohlcv_fast) < 50 or len(ohlcv_slow) < 30:
        return None

    opens = [c[1] for c in ohlcv_fast]
    highs = [c[2] for c in ohlcv_fast]
    lows = [c[3] for c in ohlcv_fast]
    closes = [c[4] for c in ohlcv_fast]

    rsi_vals = rsi(closes, settings.rsi_window)
    macd_line, signal_line, hist = macd(closes, settings.macd_fast, settings.macd_slow, settings.macd_signal)
    atr_vals = atr(highs, lows, closes, settings.atr_window)
    # Trend filter from slow timeframe using EMA of closes
    closes_slow = [c[4] for c in ohlcv_slow]
    slow_ema = _ema(closes_slow, settings.slow_trend_ema)

    last_close = closes[-1]
    last_rsi = rsi_vals[-1]
    last_hist = hist[-1]
    last_atr = atr_vals[-1]
    last_slow_ema = slow_ema[-1] if slow_ema else None
    sup, res = micro_levels(closes, 12)

    if last_rsi is None or last_hist is None or last_atr is None or sup is None or res is None or last_slow_ema is None:
        return None

    # Volatility filter: require minimal ATR percent
    atr_pct = float(last_atr) / float(last_close)
    if atr_pct * 100.0 < settings.min_volatility_pct:
        return None

    # MACD histogram strength filter (optional)
    if settings.min_macd_hist_abs > 0 and abs(float(last_hist)) < settings.min_macd_hist_abs:
        return None

    # Breakout + momentum confirmation
    long_cond = last_close > res and last_hist > 0 and 45 < last_rsi < 75 and last_close > last_slow_ema
    short_cond = last_close < sup and last_hist < 0 and 25 < last_rsi < 55 and last_close < last_slow_ema

    # Micro swing reversals near levels with histogram flip
    bull_reversal = (
        last_close > opens[-1]
        and closes[-2] < opens[-2]
        and last_hist > 0
        and last_rsi > 40
        and last_close > sup
        and last_close > last_slow_ema
    )
    bear_reversal = (
        last_close < opens[-1]
        and closes[-2] > opens[-2]
        and last_hist < 0
        and last_rsi < 60
        and last_close < res
        and last_close < last_slow_ema
    )

    if long_cond or bull_reversal:
        return Signal("LONG", last_close, {
            "strategy": "original",
            "rsi": float(last_rsi),
            "macd_hist": float(last_hist),
            "atr": float(last_atr),
            "support": float(sup),
            "resistance": float(res),
        })

    if short_cond or bear_reversal:
        return Signal("SHORT", last_close, {
            "strategy": "original",
            "rsi": float(last_rsi),
            "macd_hist": float(last_hist),
            "atr": float(last_atr),
            "support": float(sup),
            "resistance": float(res),
        })

    return None


