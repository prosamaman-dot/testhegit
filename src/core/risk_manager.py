"""
Risk management module for calculating trade levels and risk.
"""

from dataclasses import dataclass
from typing import Optional

from src.config.settings import Settings


@dataclass
class TradeLevels:
    """Represents trade entry, stop, and take profit levels."""
    entry: float
    stop: float
    take: float
    rr: float


def clamp_sl_pct(raw_sl_pct: float) -> float:
    """Clamp stop loss percentage within allowed range."""
    settings = Settings()
    return max(settings.min_sl_pct / 100.0, min(settings.max_sl_pct / 100.0, raw_sl_pct))


def compute_levels(side: str, entry: float, atr_value: float, support: float, resistance: float) -> Optional[TradeLevels]:
    """Compute trade levels for swing trading (1-2 hours)."""
    settings = Settings()
    
    if atr_value <= 0 or entry <= 0:
        return None

    # Convert ATR to percent of price
    atr_pct = atr_value / entry
    
    # Swing trading entry price (no buffer needed for longer holds)
    entry = entry

    if side == "LONG":
        # Swing trading SL calculation (wider stops)
        level_dist = max(0.0, entry - support) / entry
        
        # Use ATR-based SL for swing trading (wider stops)
        atr_sl_pct = atr_pct * 1.5  # 150% of ATR for swing SL
        level_sl_pct = level_dist * 0.8  # 80% of level distance
        
        # Take the more conservative (larger) SL for swing trading
        raw_sl_pct = max(atr_sl_pct, level_sl_pct) if level_sl_pct > 0 else atr_sl_pct
        
        # Ensure minimum SL distance for swing trading
        raw_sl_pct = max(raw_sl_pct, 0.005)  # 0.5% minimum SL for swing trades
        
        sl_pct = clamp_sl_pct(raw_sl_pct)
        stop = entry * (1.0 - sl_pct)
        
        # Swing trading TP calculation (higher targets)
        # Use 3:1 RR for swing trading
        tp_multiplier = 3.0
        tp = entry * (1.0 + sl_pct * tp_multiplier)
        
    elif side == "SHORT":
        # Swing trading SL calculation for SHORT
        level_dist = max(0.0, resistance - entry) / entry
        
        # Use ATR-based SL for swing trading (wider stops)
        atr_sl_pct = atr_pct * 1.5  # 150% of ATR for swing SL
        level_sl_pct = level_dist * 0.8  # 80% of level distance
        
        # Take the more conservative (larger) SL for swing trading
        raw_sl_pct = max(atr_sl_pct, level_sl_pct) if level_sl_pct > 0 else atr_sl_pct
        raw_sl_pct = max(raw_sl_pct, 0.005)  # 0.5% minimum SL for swing trades
        
        sl_pct = clamp_sl_pct(raw_sl_pct)
        stop = entry * (1.0 + sl_pct)
        
        # Swing trading TP calculation (higher targets)
        tp_multiplier = 3.0
        tp = entry * (1.0 - sl_pct * tp_multiplier)
    else:
        return None

    risk = abs(entry - stop)
    reward = abs(tp - entry)
    rr = (reward / risk) if risk > 0 else 0.0
    return TradeLevels(entry=entry, stop=stop, take=tp, rr=rr)
