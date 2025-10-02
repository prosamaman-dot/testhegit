from __future__ import annotations

import asyncio
import ssl
from typing import Optional

import aiohttp

from src.config.settings import settings
from src.utils.simple_logger import create_logger


logger = create_logger(__name__)


class TelegramNotifier:
    """Telegram notification handler."""
    
    async def send_signal_message(self, symbol: str, side: str, entry: float, 
                                stop: float, take: float, rr: float, strategy: str) -> Optional[int]:
        """Send trading signal message with copyable prices."""
        # Format as plain text to avoid parsing errors
        text = f"🚀 {side} SIGNAL - {symbol}\n"
        text += f"========================\n\n"
        text += f"📍 Entry: {entry:.6f}\n"
        text += f"🛑 Stop Loss: {stop:.6f}\n"
        text += f"🎯 Take Profit: {take:.6f}\n"
        text += f"📊 Risk/Reward: 1:{rr:.2f}\n"
        text += f"🔧 Strategy: {strategy}\n\n"
        text += f"💡 Tap prices to copy"
        
        message_id = await send_telegram_message(text)
        return message_id
    
    async def send_close_message(self, symbol: str, side: str, reason: str, price: float, 
                                reply_to_message_id: Optional[int] = None) -> Optional[int]:
        """Send position close message with reply to original signal."""
        emoji = "✅" if reason == "TP" else "🛑" if reason == "SL" else "⚖️"
        text = f"{emoji} {side} {reason} HIT - {symbol}\n"
        text += f"========================\n\n"
        text += f"💰 Exit Price: {price:.6f}"
        
        return await send_telegram_message(text, reply_to_message_id)


def _create_ssl_context():
    """Create SSL context with better compatibility."""
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context


def _create_connector():
    """Create aiohttp connector with better error handling."""
    connector = aiohttp.TCPConnector(
        ssl=_create_ssl_context(),
        limit=10,
        limit_per_host=5,
        ttl_dns_cache=300,
        use_dns_cache=True,
        enable_cleanup_closed=True,
        family=0  # Use both IPv4 and IPv6
    )
    return connector


async def _send_telegram_with_retry(text: str, reply_to_message_id: Optional[int] = None, 
                                   parse_mode: str = None, max_retries: int = 3) -> Optional[int]:
    """Send Telegram message with retry logic and multiple fallback methods."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.debug("Telegram not configured; skipping message: %s", text)
        return None
    
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "disable_web_page_preview": False
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id
        payload["allow_sending_without_reply"] = True
    
    for attempt in range(max_retries):
        try:
            # Use simpler timeout and connector
            timeout = aiohttp.ClientTimeout(total=30, connect=15)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        message_id = data.get("result", {}).get("message_id")
                        logger.debug("Telegram message sent successfully")
                        return message_id
                    else:
                        body = await resp.text()
                        logger.warning("Telegram API error %s: %s", resp.status, body)
                        
        except Exception as exc:
            logger.warning("Telegram send attempt %d failed: %s", attempt + 1, exc)
            
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.info("Retrying Telegram send in %d seconds...", wait_time)
            await asyncio.sleep(wait_time)
    
    logger.error("All Telegram send attempts failed")
    return None


def _fmt_price(value: float) -> str:
    if value >= 1:
        return f"{value:.4f}"
    return f"{value:.6f}"


def _fmt_price_with_dollar(value: float) -> str:
    if value >= 1:
        return f"${value:.4f}"
    return f"${value:.6f}"


def format_signal_message(symbol: str, side: str, entry: float, stop: float, take: float, rr: float, strategy: str = "") -> str:
    emoji = "🚀" if side.upper() == "LONG" else "🔻"
    rr_str = f"1:{rr:.2f}" if rr > 0 else "-"
    strategy_text = f" [{strategy.upper()}]" if strategy else ""
    
    # Format with code blocks for easy copy (no $ symbols)
    entry_code = f"`{_fmt_price(entry)}`"
    sl_code = f"`{_fmt_price(stop)}`"
    tp_code = f"`{_fmt_price(take)}`"
    
    return (
        f"{emoji} **{side.upper()} SIGNAL**{strategy_text} - **{symbol}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 **Entry:** {entry_code}\n"
        f"🛑 **Stop Loss:** {sl_code}\n"
        f"🎯 **Take Profit:** {tp_code}\n"
        f"📊 **Risk/Reward:** {rr_str}\n\n"
        f"💡 Tap prices to copy"
    )


def format_close_message(symbol: str, side: str, level: str, price: float) -> str:
    emoji = "✅" if level == "TP" else "🛑"
    side_txt = "LONG" if side.upper() == "LONG" else "SHORT"
    price_code = f"`{_fmt_price(price)}`"
    
    return (
        f"{emoji} **{side_txt} {level} HIT** - **{symbol}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 **Exit Price:** {price_code}"
    )


async def send_telegram_message(text: str, reply_to_message_id: Optional[int] = None, parse_mode: str = None) -> Optional[int]:
    """Send message to main chat only (no duplicates)."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.debug("Telegram not configured; skipping message: %s", text)
        return None
    
    # Send to main chat only to avoid duplicates
    main_msg_id = await _send_telegram_with_retry(text, reply_to_message_id, parse_mode)
    
    return main_msg_id


async def test_telegram_connection() -> bool:
    """Test Telegram connection and return True if successful."""
    test_message = "Bot connection test - Telegram is working!"
    try:
        result = await _send_telegram_with_retry(test_message, max_retries=1)
        if result:
            logger.info("Telegram connection test successful!")
            return True
        else:
            logger.error("Telegram connection test failed")
            return False
    except Exception as e:
        logger.error("Telegram connection test error: %s", e)
        return False


