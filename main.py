#!/usr/bin/env python3
"""
Scalper Bot - Professional Trading Bot
Main entry point for the trading bot application.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.bot import ScalperBot
# No setup_logging needed

async def main():
    """Main entry point for the scalper bot."""
    # Create and run the bot
    bot = ScalperBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot crashed: {e}")
        sys.exit(1)
