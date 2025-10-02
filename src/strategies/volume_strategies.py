"""
Advanced volume-based trading strategies for VIP-level performance.
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.config.settings import settings
from src.utils.simple_logger import create_logger

logger = create_logger(__name__)


@dataclass
class VolumeSignal:
    side: str
    entry: float
    confidence: float
    volume_ratio: float
    context: Dict[str, Any]


def calculate_volume_ma(volumes: np.ndarray, periods: int) -> np.ndarray:
    """Calculate volume moving average."""
    if len(volumes) < periods:
        return np.full_like(volumes, np.nan)
    
    result = np.full_like(volumes, np.nan)
    for i in range(periods - 1, len(volumes)):
        result[i] = np.mean(volumes[i - periods + 1:i + 1])
    
    return result


def detect_volume_spike(ohlcv: np.ndarray) -> Optional[VolumeSignal]:
    """
    Detect volume spikes that often precede price movements.
    Returns signal when volume is significantly above average.
    """
    if len(ohlcv) < settings.volume_lookback_periods + 1:
        return None
    
    # Convert to numpy array if it's a list of lists
    if isinstance(ohlcv, list):
        ohlcv = np.array(ohlcv)
    
    volumes = ohlcv[:, 5]  # Volume column
    prices = ohlcv[:, 4]   # Close prices
    
    # Calculate volume moving average
    volume_ma = calculate_volume_ma(volumes, settings.volume_lookback_periods)
    
    if np.isnan(volume_ma[-1]) or volume_ma[-1] == 0:
        return None
    
    # Calculate volume ratio
    current_volume = volumes[-1]
    avg_volume = volume_ma[-1]
    volume_ratio = current_volume / avg_volume
    
    # Check if volume spike is significant
    if volume_ratio < settings.volume_spike_threshold:
        return None
    
    # Determine direction based on price movement
    current_price = prices[-1]
    prev_price = prices[-2]
    price_change = (current_price - prev_price) / prev_price
    
    # Strong volume with price movement
    if abs(price_change) > 0.001:  # 0.1% minimum price change
        side = "LONG" if price_change > 0 else "SHORT"
        confidence = min(volume_ratio / settings.volume_spike_threshold, 2.0)  # Cap at 2.0
        
        return VolumeSignal(
            side=side,
            entry=current_price,
            confidence=confidence,
            volume_ratio=volume_ratio,
            context={
                "strategy": "volume_spike",
                "volume_ratio": volume_ratio,
                "price_change_pct": price_change * 100,
                "avg_volume": avg_volume,
                "current_volume": current_volume
            }
        )
    
    return None


def detect_breakout(ohlcv: np.ndarray) -> Optional[VolumeSignal]:
    """
    Detect price breakouts with volume confirmation.
    Looks for price breaking above/below recent highs/lows with volume.
    """
    if len(ohlcv) < settings.breakout_lookback_periods + settings.breakout_confirmation_candles:
        return None
    
    # Convert to numpy array if it's a list of lists
    if isinstance(ohlcv, list):
        ohlcv = np.array(ohlcv)
    
    highs = ohlcv[:, 2]  # High prices
    lows = ohlcv[:, 3]   # Low prices
    closes = ohlcv[:, 4] # Close prices
    volumes = ohlcv[:, 5] # Volumes
    
    # Calculate recent high and low
    recent_high = np.max(highs[-settings.breakout_lookback_periods:-settings.breakout_confirmation_candles])
    recent_low = np.min(lows[-settings.breakout_lookback_periods:-settings.breakout_confirmation_candles])
    
    # Check for breakout in confirmation period
    confirmation_highs = highs[-settings.breakout_confirmation_candles:]
    confirmation_lows = lows[-settings.breakout_confirmation_candles:]
    confirmation_volumes = volumes[-settings.breakout_confirmation_candles:]
    
    # Check for upward breakout
    if np.any(confirmation_highs > recent_high):
        # Verify with volume
        avg_volume = np.mean(volumes[-settings.volume_lookback_periods:])
        breakout_volume = np.mean(confirmation_volumes)
        
        if breakout_volume > avg_volume * 1.5:  # 50% above average volume
            return VolumeSignal(
                side="LONG",
                entry=closes[-1],
                confidence=1.5,
                volume_ratio=breakout_volume / avg_volume,
                context={
                    "strategy": "breakout",
                    "breakout_level": recent_high,
                    "volume_ratio": breakout_volume / avg_volume,
                    "confirmation_candles": settings.breakout_confirmation_candles
                }
            )
    
    # Check for downward breakout
    if np.any(confirmation_lows < recent_low):
        # Verify with volume
        avg_volume = np.mean(volumes[-settings.volume_lookback_periods:])
        breakout_volume = np.mean(confirmation_volumes)
        
        if breakout_volume > avg_volume * 1.5:  # 50% above average volume
            return VolumeSignal(
                side="SHORT",
                entry=closes[-1],
                confidence=1.5,
                volume_ratio=breakout_volume / avg_volume,
                context={
                    "strategy": "breakout",
                    "breakout_level": recent_low,
                    "volume_ratio": breakout_volume / avg_volume,
                    "confirmation_candles": settings.breakout_confirmation_candles
                }
            )
    
    return None


def calculate_heikin_ashi(ohlcv: np.ndarray) -> np.ndarray:
    """
    Calculate Heikin Ashi candles for smoother trend analysis.
    Returns array with [open, high, low, close] for each candle.
    """
    if len(ohlcv) < 2:
        return ohlcv[:, :4]  # Return original if not enough data
    
    # Convert to numpy array if it's a list of lists
    if isinstance(ohlcv, list):
        ohlcv = np.array(ohlcv)
    
    opens = ohlcv[:, 1]
    highs = ohlcv[:, 2]
    lows = ohlcv[:, 3]
    closes = ohlcv[:, 4]
    
    ha_opens = np.zeros_like(opens)
    ha_highs = np.zeros_like(highs)
    ha_lows = np.zeros_like(lows)
    ha_closes = np.zeros_like(closes)
    
    # First candle is same as original
    ha_opens[0] = opens[0]
    ha_highs[0] = highs[0]
    ha_lows[0] = lows[0]
    ha_closes[0] = closes[0]
    
    # Calculate Heikin Ashi for subsequent candles
    for i in range(1, len(ohlcv)):
        # HA Close = (O + H + L + C) / 4
        ha_closes[i] = (opens[i] + highs[i] + lows[i] + closes[i]) / 4
        
        # HA Open = (Previous HA Open + Previous HA Close) / 2
        ha_opens[i] = (ha_opens[i-1] + ha_closes[i-1]) / 2
        
        # HA High = max(H, HA Open, HA Close)
        ha_highs[i] = max(highs[i], ha_opens[i], ha_closes[i])
        
        # HA Low = min(L, HA Open, HA Close)
        ha_lows[i] = min(lows[i], ha_opens[i], ha_closes[i])
    
    return np.column_stack([ha_opens, ha_highs, ha_lows, ha_closes])


def detect_heikin_ashi_trend(ohlcv: np.ndarray) -> Optional[VolumeSignal]:
    """
    Detect trends using Heikin Ashi candles for smoother analysis.
    """
    if len(ohlcv) < settings.heikin_ashi_trend_periods + 1:
        return None
    
    # Convert to numpy array if it's a list of lists
    if isinstance(ohlcv, list):
        ohlcv = np.array(ohlcv)
    
    ha_candles = calculate_heikin_ashi(ohlcv)
    ha_opens = ha_candles[:, 0]
    ha_closes = ha_candles[:, 1]
    
    # Check recent trend
    recent_opens = ha_opens[-settings.heikin_ashi_trend_periods:]
    recent_closes = ha_closes[-settings.heikin_ashi_trend_periods:]
    
    # Count bullish and bearish candles
    bullish_candles = np.sum(recent_closes > recent_opens)
    bearish_candles = np.sum(recent_closes < recent_opens)
    
    # Need strong trend (at least 80% in one direction)
    total_candles = len(recent_opens)
    bullish_ratio = bullish_candles / total_candles
    bearish_ratio = bearish_candles / total_candles
    
    if bullish_ratio >= 0.8:
        return VolumeSignal(
            side="LONG",
            entry=ohlcv[-1, 4],  # Current close price
            confidence=bullish_ratio,
            volume_ratio=1.0,
            context={
                "strategy": "heikin_ashi",
                "trend_strength": bullish_ratio,
                "bullish_candles": bullish_candles,
                "total_candles": total_candles
            }
        )
    elif bearish_ratio >= 0.8:
        return VolumeSignal(
            side="SHORT",
            entry=ohlcv[-1, 4],  # Current close price
            confidence=bearish_ratio,
            volume_ratio=1.0,
            context={
                "strategy": "heikin_ashi",
                "trend_strength": bearish_ratio,
                "bearish_candles": bearish_candles,
                "total_candles": total_candles
            }
        )
    
    return None


def generate_volume_signal(ohlcv_fast, ohlcv_slow):
    """
    Generate trading signal based on volume analysis.
    Returns a Signal object compatible with the main strategy system.
    """
    if ohlcv_fast is None or ohlcv_slow is None:
        return None
    
    # Convert to numpy arrays if they're lists
    if isinstance(ohlcv_fast, list):
        ohlcv_fast = np.array(ohlcv_fast)
    if isinstance(ohlcv_slow, list):
        ohlcv_slow = np.array(ohlcv_slow)
    
    # Try different volume-based strategies
    strategies = [
        detect_volume_spike,
        detect_breakout,
        detect_heikin_ashi_trend
    ]
    
    for strategy in strategies:
        try:
            volume_signal = strategy(ohlcv_fast)
            if volume_signal:
                logger.debug("Volume strategy %s generated signal: %s", 
                           volume_signal.context.get("strategy", "unknown"), volume_signal.side)
                
                # Convert VolumeSignal to Signal format
                from strategy import Signal
                return Signal(
                    side=volume_signal.side,
                    entry=volume_signal.entry,
                    context={
                        "strategy": volume_signal.context.get("strategy", "volume"),
                        "atr": 0.0,  # Will be calculated by main system
                        "support": 0.0,
                        "resistance": 0.0,
                        **volume_signal.context  # Include all volume-specific context
                    }
                )
        except Exception as e:
            logger.warning("Volume strategy %s failed: %s", strategy.__name__, e)
            continue
    
    return None
