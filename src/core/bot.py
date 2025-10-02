"""
Main Scalper Bot class - Core trading logic.
"""

import asyncio
import time
from typing import Dict, List

from src.config.settings import Settings
from src.data.fetcher import DataFetcher
from src.strategies.signal_generator import SignalGenerator
from src.notifications.telegram import TelegramNotifier
from src.notifications.news_feed import NewsFeed
from src.utils.simple_logger import create_logger

logger = create_logger(__name__)


class OpenSignal:
    """Represents an open trading signal."""
    def __init__(self, side: str, levels, message_id: int, entry_ts: float, symbol: str):
        self.side = side
        self.levels = levels
        self.message_id = message_id
        self.entry_ts = entry_ts
        self.symbol = symbol
        self.breakeven_moved = False


class ScalperBot:
    """Main scalper bot class."""
    
    def __init__(self):
        self.settings = Settings()
        self.data_fetcher = DataFetcher()
        self.signal_generator = SignalGenerator()
        self.telegram_notifier = TelegramNotifier()
        self.news_feed = NewsFeed()
        
    async def run(self):
        """Main bot execution loop."""
        symbols = self._get_symbols()
        logger.info("Starting scalper bot | Exchange=%s | Symbols=%s", 
                   self.settings.exchange, ", ".join(symbols))
        
        # Initialize data fetcher
        try:
            await self.data_fetcher.warmup()
            logger.info("Using real exchange: %s", self.settings.exchange)
        except Exception as e:
            logger.warning("Real exchange failed (%s), using mock data: %s", 
                          self.settings.exchange, e)
            await self.data_fetcher.warmup_mock()
        
        # Start news feed
        await self.news_feed.start()
        
        # Manage open positions per symbol
        open_positions: Dict[str, OpenSignal] = {}
        last_stop_time: float = 0.0
        last_signal_time: float = 0.0  # Track last signal time for cooldown
        
        
        try:
            while True:
                try:
                    # Fetch recent data fast
                    results = await self._fetch_all_data(symbols)
                    
                    # Check if we have valid data
                    any_valid = any((f and s and p is not None) for (_, p, f, s, m) in results)
                    if not any_valid:
                        await asyncio.sleep(self.settings.loop_interval_sec)
                        continue
                    
                    # Manage existing positions
                    await self._manage_existing_positions(open_positions, results, last_stop_time)
                    
                    # Generate new signals
                    await self._generate_new_signals(
                        open_positions, results, last_stop_time, last_signal_time
                    )
                    
                except Exception as loop_exc:
                    logger.warning("Loop error: %s", loop_exc)
                    await asyncio.sleep(self.settings.loop_interval_sec)
                    
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error("Bot crashed: %s", e)
            raise
    
    def _get_symbols(self) -> List[str]:
        """Get list of trading symbols."""
        return [s.strip() for s in self.settings.symbols_csv.split(',') if s.strip()]
    
    async def _fetch_all_data(self, symbols: List[str]):
        """Fetch data for all symbols in parallel."""
        async def fetch_for(sym: str):
            p = await self.data_fetcher.fetch_price(sym)
            f = await self.data_fetcher.fetch_ohlcv(sym, self.settings.tf_fast, self.settings.candles_limit)
            s = await self.data_fetcher.fetch_ohlcv(sym, self.settings.tf_slow, self.settings.candles_limit)
            m = await self.data_fetcher.fetch_ohlcv(sym, self.settings.tf_medium, self.settings.candles_limit)
            return sym, p, f, s, m
        
        return await asyncio.gather(*[fetch_for(sym) for sym in symbols])
    
    async def _manage_existing_positions(self, open_positions: Dict[str, OpenSignal], 
                                       results, last_stop_time: float):
        """Manage existing open positions."""
        for sym, p, f, s, m in results:
            if sym not in open_positions or p is None:
                continue
                
            pos = open_positions[sym]
            px = float(p)
            side = pos.side
            lv = pos.levels
            
            # Move to breakeven when price moves favorably
            if not pos.breakeven_moved:
                if side == "LONG" and px >= lv.entry * (1.0 + (lv.entry - lv.stop) * self.settings.breakeven_trigger_r / lv.entry):
                    # Move SL to breakeven
                    lv.stop = lv.entry
                    pos.breakeven_moved = True
                    logger.info("Moved %s %s to breakeven at %.6f", side, sym, lv.entry)
                elif side == "SHORT" and px <= lv.entry * (1.0 - (lv.stop - lv.entry) * self.settings.breakeven_trigger_r / lv.entry):
                    # Move SL to breakeven
                    lv.stop = lv.entry
                    pos.breakeven_moved = True
                    logger.info("Moved %s %s to breakeven at %.6f", side, sym, lv.entry)
            
            # Check for stop loss or take profit
            if side == "LONG":
                if px <= lv.stop:
                    # Stop loss hit
                    result = "SL" if px < lv.entry else "BE"  # Breakeven if at entry
                    await self.telegram_notifier.send_close_message(sym, side, result, px, pos.message_id)
                    open_positions.pop(sym, None)
                    last_stop_time = time.time()
                elif px >= lv.take:
                    # Take profit hit
                    await self.telegram_notifier.send_close_message(sym, side, "TP", px, pos.message_id)
                    open_positions.pop(sym, None)
                    last_stop_time = 0.0
            else:  # SHORT
                if px >= lv.stop:
                    # Stop loss hit
                    result = "SL" if px > lv.entry else "BE"  # Breakeven if at entry
                    await self.telegram_notifier.send_close_message(sym, side, result, px, pos.message_id)
                    open_positions.pop(sym, None)
                    last_stop_time = time.time()
                elif px <= lv.take:
                    # Take profit hit
                    await self.telegram_notifier.send_close_message(sym, side, "TP", px, pos.message_id)
                    open_positions.pop(sym, None)
                    last_stop_time = 0.0
    
    async def _generate_new_signals(self, open_positions: Dict[str, OpenSignal], 
                                  results, last_stop_time: float, last_signal_time: float):
        """Generate new trading signals."""
        # Cooldown checks
        cooldown_active = last_stop_time > 0 and (time.time() - last_stop_time) < self.settings.cooldown_after_stop_sec
        signal_cooldown_active = last_signal_time > 0 and (time.time() - last_signal_time) < self.settings.cooldown_between_signals_sec
        
        for sym, p, f, s, m in results:
            if sym in open_positions or cooldown_active or signal_cooldown_active:
                continue
            if not f or not s or p is None:
                continue
            
            # Generate signal
            signal = await self.signal_generator.generate_signal(f, s)
            if signal is None:
                continue
            
            # Process signal
            if await self._process_signal(signal, sym, f, open_positions):
                last_signal_time = time.time()
    
    async def _process_signal(self, signal, sym: str, f, open_positions: Dict[str, OpenSignal]) -> bool:
        """Process a trading signal and send notification if valid."""
        from src.core.risk_manager import compute_levels
        
        # Calculate ATR if not provided
        atr_est = signal.context.get("atr", 0.0)
        if atr_est <= 0:
            from src.strategies.indicators import atr
            highs = [c[2] for c in f]
            lows = [c[3] for c in f]
            closes = [c[4] for c in f]
            atr_vals = atr(highs, lows, closes, self.settings.atr_window)
            atr_est = atr_vals[-1] if atr_vals and atr_vals[-1] is not None else 0.0
        
        # Calculate support/resistance if not provided
        support = signal.context.get("support", 0.0)
        resistance = signal.context.get("resistance", 0.0)
        if support <= 0 or resistance <= 0:
            from src.strategies.indicators import micro_levels
            closes = [c[4] for c in f]
            sup, res = micro_levels(closes, 12)
            support = sup if sup is not None else 0.0
            resistance = res if res is not None else 0.0
        
        # Compute trade levels
        levels = compute_levels(signal.side, signal.entry, atr_est, support, resistance)
        
        if not levels:
            logger.debug("No levels computed for signal %s for %s", signal.side, sym)
            return False
        
        # Check if signal meets quality criteria
        if levels.rr < self.settings.target_rr:
            logger.debug("Signal %s for %s rejected: RR %.2f below threshold %.2f", 
                        signal.side, sym, levels.rr, self.settings.target_rr)
            return False
        
        # Additional quality filters
        atr_pct = (atr_est / signal.entry) * 100
        if atr_pct < self.settings.min_volatility_pct:
            logger.debug("Signal %s for %s rejected: volatility too low (%.2f%%)", 
                        signal.side, sym, atr_pct)
            return False
        
        # Send signal notification and get message ID
        strategy_name = signal.context.get("strategy", "unknown")
        message_id = await self.telegram_notifier.send_signal_message(
            sym, signal.side, levels.entry, levels.stop, levels.take, levels.rr, strategy_name
        )
        
        logger.info("New %s signal %s [%s] at %.6f (SL %.6f / TP %.6f / RR %.2f)", 
                   signal.side, sym, strategy_name, levels.entry, levels.stop, levels.take, levels.rr)
        
        # Add position to tracking with message ID
        open_positions[sym] = OpenSignal(
            side=signal.side,
            levels=levels,
            message_id=message_id or 0,  # Store the actual message ID
            entry_ts=time.time(),
            symbol=sym
        )
        
        return True
    
