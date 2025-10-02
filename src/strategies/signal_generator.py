"""
Signal generator for trading strategies.
"""

from typing import List, Optional
from src.config.settings import Settings
from src.strategies.indicators import Signal
from src.utils.simple_logger import create_logger

logger = create_logger(__name__)


class SignalGenerator:
    """Generates trading signals using various strategies."""
    
    def __init__(self):
        self.settings = Settings()
    
    async def generate_signal(self, ohlcv_fast: List[List[float]], 
                            ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """Generate trading signal using active strategies."""
        if len(ohlcv_fast) < 50 or len(ohlcv_slow) < 30:
            return None

        # Get active strategies from config
        active_strategies = [s.strip() for s in self.settings.active_strategies.split(',') if s.strip()]
        
        # Try each strategy in order until one generates a signal
        for strategy_name in active_strategies:
            signal = None
            
            if strategy_name == "triple_ema":
                signal = self._triple_ema_signal(ohlcv_fast, ohlcv_slow)
            elif strategy_name == "bb_squeeze":
                signal = self._bb_squeeze_signal(ohlcv_fast, ohlcv_slow)
            elif strategy_name == "breakout_retest":
                signal = self._breakout_retest_signal(ohlcv_fast, ohlcv_slow)
            elif strategy_name == "vwap_fade":
                signal = self._vwap_fade_signal(ohlcv_fast, ohlcv_slow)
            elif strategy_name == "fast_macd":
                signal = self._fast_macd_signal(ohlcv_fast, ohlcv_slow)
            elif strategy_name == "range_scalp":
                signal = self._range_scalp_signal(ohlcv_fast, ohlcv_slow)
            elif strategy_name == "keltner_stoch":
                signal = self._keltner_stoch_signal(ohlcv_fast, ohlcv_slow)
            elif strategy_name == "vwap_ema_confluence":
                signal = self._vwap_ema_confluence_signal(ohlcv_fast, ohlcv_slow)
            elif strategy_name == "original":
                signal = self._original_signal(ohlcv_fast, ohlcv_slow)
            
            if signal is not None:
                logger.debug("Strategy %s generated signal: %s", strategy_name, signal.side)
                return signal
        
        return None
    
    def _triple_ema_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """Triple EMA trend/pullback strategy."""
        from src.strategies.indicators import triple_ema_signal
        return triple_ema_signal(ohlcv_fast, ohlcv_slow)
    
    def _bb_squeeze_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """Bollinger Bands squeeze strategy."""
        from src.strategies.indicators import bb_squeeze_signal
        return bb_squeeze_signal(ohlcv_fast, ohlcv_slow)
    
    def _breakout_retest_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """Breakout retest strategy."""
        from src.strategies.indicators import breakout_retest_signal
        return breakout_retest_signal(ohlcv_fast, ohlcv_slow)
    
    def _vwap_fade_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """VWAP fade strategy."""
        from src.strategies.indicators import vwap_fade_signal
        return vwap_fade_signal(ohlcv_fast, ohlcv_slow)
    
    def _fast_macd_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """Fast MACD strategy."""
        from src.strategies.indicators import fast_macd_signal
        return fast_macd_signal(ohlcv_fast, ohlcv_slow)
    
    def _range_scalp_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """Range scalp strategy."""
        from src.strategies.indicators import range_scalp_signal
        return range_scalp_signal(ohlcv_fast, ohlcv_slow)
    
    def _keltner_stoch_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """Keltner Channel + Stochastic strategy."""
        from src.strategies.indicators import keltner_stoch_signal
        return keltner_stoch_signal(ohlcv_fast, ohlcv_slow)
    
    def _vwap_ema_confluence_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """VWAP + EMA confluence strategy."""
        from src.strategies.indicators import vwap_ema_confluence_signal
        return vwap_ema_confluence_signal(ohlcv_fast, ohlcv_slow)
    
    def _original_signal(self, ohlcv_fast: List[List[float]], ohlcv_slow: List[List[float]]) -> Optional[Signal]:
        """Original strategy for backward compatibility."""
        from src.strategies.indicators import original_signal
        return original_signal(ohlcv_fast, ohlcv_slow)
