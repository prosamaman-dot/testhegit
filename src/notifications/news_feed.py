"""
Crypto news feed for sending market news alerts to Telegram.
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import aiohttp
from src.config.settings import Settings
from src.utils.simple_logger import create_logger

logger = create_logger(__name__)


class NewsItem:
    """Represents a single news item."""
    
    def __init__(self, title: str, summary: str, url: str, published_at: str, source: str):
        self.title = title
        self.summary = summary
        self.url = url
        self.published_at = published_at
        self.source = source
        self.timestamp = time.time()
        self.sentiment = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
        self.quality_score = 10  # 1-10 rating
        self.freshness_score = 10  # 1-10 rating


class NewsFeed:
    """Crypto news feed that fetches and sends news alerts."""
    
    def __init__(self):
        self.settings = Settings()
        self.last_check_time = time.time()
        self.sent_news = set()  # Track sent news to avoid duplicates
        self.session = None
        self.surprise_count = 0  # Counter for surprise features
        
    async def start(self):
        """Start the news feed in background."""
        if not self.settings.news_enabled:
            logger.info("News feed disabled in settings")
            return
            
        logger.info("Crypto news feed started - checking every %d seconds", 
                   self.settings.news_check_interval)
        
        # Start news checking loop
        asyncio.create_task(self._news_loop())
    
    async def _news_loop(self):
        """Main news checking loop."""
        while True:
            try:
                await self._check_news()
                await asyncio.sleep(self.settings.news_check_interval)
            except Exception as e:
                logger.error("News loop error: %s", e)
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_news(self):
        """Check for new crypto news and send alerts."""
        try:
            logger.info("Checking for fresh crypto news...")
            
            # Fetch news from multiple sources
            news_items = []
            
            # Try CryptoCompare first
            try:
                cc_news = await self._fetch_cryptocompare_news()
                news_items.extend(cc_news)
            except Exception as e:
                logger.warning("CryptoCompare news failed: %s", e)
            
            # Try CoinDesk as backup
            try:
                cd_news = await self._fetch_coindesk_news()
                news_items.extend(cd_news)
            except Exception as e:
                logger.warning("CoinDesk news failed: %s", e)
            
            if not news_items:
                logger.info("No news found from any source")
                return
            
            # Filter for high-impact news and analyze sentiment
            high_impact = self._filter_high_impact_news(news_items)
            
            if high_impact:
                logger.info("Found %d high-impact news items", len(high_impact))
                await self._send_news_alerts(high_impact)
            else:
                logger.info("No high-impact news found")
                
            # Check for surprise feature
            await self._check_surprise_feature()
                
        except Exception as e:
            logger.error("News check error: %s", e)
    
    async def _fetch_cryptocompare_news(self) -> List[NewsItem]:
        """Fetch news from CryptoCompare API."""
        url = "https://min-api.cryptocompare.com/data/v2/news/"
        params = {
            'lang': 'EN',
            'sortOrder': 'latest',
            'limit': 20
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('Type') == 100 and data.get('Data'):
                        news_items = []
                        for item in data['Data'][:10]:  # Limit to 10 items
                            news_item = NewsItem(
                                title=item.get('title', ''),
                                summary=item.get('body', '')[:200] + '...' if len(item.get('body', '')) > 200 else item.get('body', ''),
                                url=item.get('url', ''),
                                published_at=item.get('published_on', ''),
                                source='CryptoCompare'
                            )
                            # Analyze sentiment and quality
                            news_item.sentiment = self._analyze_sentiment(news_item)
                            news_item.quality_score = self._calculate_quality_score(news_item)
                            news_item.freshness_score = self._calculate_freshness_score(news_item)
                            news_items.append(news_item)
                        return news_items
        return []
    
    async def _fetch_coindesk_news(self) -> List[NewsItem]:
        """Fetch news from CoinDesk RSS feed."""
        # For now, return empty list as CoinDesk requires more complex parsing
        # This can be implemented later if needed
        return []
    
    def _filter_high_impact_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Filter news for high-impact keywords and 10/10 quality."""
        high_impact_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency',
            'regulation', 'sec', 'sec', 'fed', 'federal', 'inflation',
            'adoption', 'institutional', 'etf', 'halving', 'bull', 'bear',
            'market', 'trading', 'exchange', 'binance', 'coinbase',
            'breakthrough', 'milestone', 'partnership', 'launch', 'upgrade'
        ]
        
        filtered = []
        for item in news_items:
            # Only accept 10/10 quality news
            if item.quality_score < 10 or item.freshness_score < 10:
                continue
                
            # Check if news is very fresh (within last 30 minutes)
            if time.time() - item.timestamp > 1800:  # 30 minutes
                continue
                
            # Check for high-impact keywords
            text = (item.title + ' ' + item.summary).lower()
            if any(keyword in text for keyword in high_impact_keywords):
                # Avoid duplicates
                news_id = f"{item.title}_{item.published_at}"
                if news_id not in self.sent_news:
                    filtered.append(item)
                    self.sent_news.add(news_id)
        
        return filtered[:2]  # Limit to 2 news items per check (only 10/10 quality)
    
    def _analyze_sentiment(self, item: NewsItem) -> str:
        """Analyze news sentiment for bullish/bearish recommendation."""
        text = (item.title + ' ' + item.summary).lower()
        
        # Bullish keywords
        bullish_keywords = [
            'bull', 'bullish', 'surge', 'rally', 'moon', 'pump', 'breakout',
            'adoption', 'institutional', 'etf', 'approval', 'partnership',
            'upgrade', 'launch', 'milestone', 'breakthrough', 'record',
            'high', 'gain', 'profit', 'positive', 'optimistic', 'growth'
        ]
        
        # Bearish keywords
        bearish_keywords = [
            'bear', 'bearish', 'crash', 'dump', 'fall', 'decline', 'drop',
            'regulation', 'ban', 'warning', 'risk', 'volatility', 'uncertainty',
            'negative', 'pessimistic', 'concern', 'fear', 'sell', 'loss'
        ]
        
        bullish_count = sum(1 for keyword in bullish_keywords if keyword in text)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in text)
        
        if bullish_count > bearish_count:
            return "BULLISH"
        elif bearish_count > bullish_count:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _calculate_quality_score(self, item: NewsItem) -> int:
        """Calculate quality score (1-10) for news item."""
        score = 5  # Base score
        
        # Title quality
        if len(item.title) > 20 and len(item.title) < 100:
            score += 1
        
        # Summary quality
        if len(item.summary) > 50:
            score += 1
        
        # Source quality
        if item.source == 'CryptoCompare':
            score += 2
        
        # Keyword density
        text = (item.title + ' ' + item.summary).lower()
        important_keywords = ['bitcoin', 'ethereum', 'crypto', 'regulation', 'market']
        keyword_count = sum(1 for keyword in important_keywords if keyword in text)
        score += min(keyword_count, 2)
        
        return min(score, 10)  # Cap at 10
    
    def _calculate_freshness_score(self, item: NewsItem) -> int:
        """Calculate freshness score (1-10) for news item."""
        age_minutes = (time.time() - item.timestamp) / 60
        
        if age_minutes <= 5:
            return 10
        elif age_minutes <= 15:
            return 9
        elif age_minutes <= 30:
            return 8
        elif age_minutes <= 60:
            return 7
        else:
            return 5
    
    async def _check_surprise_feature(self):
        """Check if it's time for a surprise feature."""
        self.surprise_count += 1
        
        # Send surprise every 10th news check (every 5 hours)
        if self.surprise_count % 10 == 0:
            await self._send_surprise_feature()
    
    async def _send_surprise_feature(self):
        """Send a surprise feature to the user."""
        surprises = [
            "🎉 SURPRISE! 🎉\n\n📊 **MARKET INSIGHT**\nBitcoin dominance is at a critical level. Watch for potential altcoin season!",
            "🎁 SURPRISE! 🎁\n\n💡 **TRADING TIP**\nThe best time to enter trades is during high volatility periods. Patience pays!",
            "🎊 SURPRISE! 🎊\n\n📈 **MARKET ANALYSIS**\nInstitutional adoption is accelerating. This could be the start of a new bull cycle!",
            "🎯 SURPRISE! 🎯\n\n⚡ **QUICK INSIGHT**\nVolume spikes often precede major price movements. Keep an eye on unusual activity!",
            "🌟 SURPRISE! 🌟\n\n🔮 **PREDICTION**\nBased on current market structure, we might see a significant move in the next 24-48 hours!"
        ]
        
        surprise = random.choice(surprises)
        
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            return
        
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.settings.telegram_chat_id,
            "text": surprise,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.info("Sent surprise feature!")
        except Exception as e:
            logger.error("Failed to send surprise: %s", e)
    
    async def _send_news_alerts(self, news_items: List[NewsItem]):
        """Send news alerts to Telegram."""
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            logger.warning("Telegram not configured for news alerts")
            return
        
        for item in news_items:
            try:
                await self._send_news_message(item)
                await asyncio.sleep(1)  # Small delay between messages
            except Exception as e:
                logger.error("Failed to send news alert: %s", e)
    
    async def _send_news_message(self, item: NewsItem):
        """Send a single news message to Telegram."""
        # Get sentiment emoji and recommendation
        if item.sentiment == "BULLISH":
            sentiment_emoji = "🟢"
            recommendation = "BULLISH 📈"
        elif item.sentiment == "BEARISH":
            sentiment_emoji = "🔴"
            recommendation = "BEARISH 📉"
        else:
            sentiment_emoji = "🟡"
            recommendation = "NEUTRAL ⚖️"
        
        # Format the news message
        text = f"📰 **CRYPTO NEWS ALERT** {sentiment_emoji}\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"**{item.title}**\n\n"
        text += f"📝 {item.summary}\n\n"
        text += f"🎯 **RECOMMENDATION:** {recommendation}\n"
        text += f"⭐ **QUALITY:** {item.quality_score}/10\n"
        text += f"🕐 **FRESHNESS:** {item.freshness_score}/10\n"
        text += f"⏰ **POSTED:** {datetime.fromtimestamp(item.timestamp).strftime('%H:%M:%S')}\n\n"
        text += f"🔗 [Read More]({item.url})\n"
        text += f"📊 Source: {item.source}"
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.settings.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    logger.info("Sent news alert: %s", item.title[:50])
                else:
                    logger.warning("Failed to send news alert: %s", await response.text())
