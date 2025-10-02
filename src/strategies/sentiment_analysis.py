"""
Social sentiment analysis for crypto trading signals.
"""

from __future__ import annotations

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.config.settings import settings
from src.utils.simple_logger import create_logger

logger = create_logger(__name__)


@dataclass
class SentimentData:
    symbol: str
    sentiment_score: float  # -1 to 1, where 1 is very positive
    confidence: float  # 0 to 1
    sources: Dict[str, float]  # sentiment from different sources
    context: Dict[str, Any]


class SentimentAnalyzer:
    """Analyze social sentiment for crypto symbols."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, SentimentData] = {}
        self.cache_timeout = 300  # 5 minutes
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_reddit_sentiment(self, symbol: str) -> Optional[float]:
        """Get sentiment from Reddit posts about the symbol."""
        if not self.session:
            return None
        
        try:
            # Simplified Reddit sentiment (in real implementation, use Reddit API)
            # For now, return a mock sentiment based on symbol
            symbol_lower = symbol.lower().replace('/usdt', '')
            
            # Mock sentiment based on symbol characteristics
            if symbol_lower in ['btc', 'bitcoin']:
                return 0.6  # Generally positive
            elif symbol_lower in ['eth', 'ethereum']:
                return 0.5  # Moderately positive
            elif symbol_lower in ['sol', 'solana']:
                return 0.7  # Very positive
            elif symbol_lower in ['doge', 'shib', 'pepe', 'bonk']:
                return 0.8  # Meme coins are very positive
            else:
                return 0.4  # Neutral to slightly positive
                
        except Exception as e:
            logger.warning("Reddit sentiment analysis failed for %s: %s", symbol, e)
            return None
    
    async def get_twitter_sentiment(self, symbol: str) -> Optional[float]:
        """Get sentiment from Twitter mentions about the symbol."""
        if not self.session:
            return None
        
        try:
            # Simplified Twitter sentiment (in real implementation, use Twitter API)
            symbol_lower = symbol.lower().replace('/usdt', '')
            
            # Mock sentiment based on symbol
            if symbol_lower in ['btc', 'bitcoin']:
                return 0.5  # Neutral to positive
            elif symbol_lower in ['eth', 'ethereum']:
                return 0.6  # Positive
            elif symbol_lower in ['sol', 'solana']:
                return 0.8  # Very positive
            elif symbol_lower in ['doge', 'shib', 'pepe', 'bonk']:
                return 0.9  # Very positive (meme coins)
            else:
                return 0.3  # Neutral
                
        except Exception as e:
            logger.warning("Twitter sentiment analysis failed for %s: %s", symbol, e)
            return None
    
    async def get_fear_greed_index(self) -> Optional[float]:
        """Get overall market sentiment from Fear & Greed Index."""
        if not self.session:
            return None
        
        try:
            # Mock Fear & Greed Index (in real implementation, use actual API)
            # Return a value between 0 and 1, where 1 is extreme greed
            return 0.6  # Currently in greed territory
            
        except Exception as e:
            logger.warning("Fear & Greed Index fetch failed: %s", e)
            return None
    
    async def analyze_sentiment(self, symbol: str) -> Optional[SentimentData]:
        """Analyze overall sentiment for a symbol."""
        if not settings.sentiment_enabled:
            return None
        
        # Check cache first
        cache_key = f"{symbol}_{asyncio.get_event_loop().time() // self.cache_timeout}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Gather sentiment from multiple sources
            sources = {}
            
            # Reddit sentiment
            reddit_sentiment = await self.get_reddit_sentiment(symbol)
            if reddit_sentiment is not None:
                sources['reddit'] = reddit_sentiment
            
            # Twitter sentiment
            twitter_sentiment = await self.get_twitter_sentiment(symbol)
            if twitter_sentiment is not None:
                sources['twitter'] = twitter_sentiment
            
            # Market sentiment
            market_sentiment = await self.get_fear_greed_index()
            if market_sentiment is not None:
                sources['market'] = market_sentiment
            
            if not sources:
                return None
            
            # Calculate weighted average sentiment
            weights = {'reddit': 0.3, 'twitter': 0.3, 'market': 0.4}
            weighted_sentiment = 0
            total_weight = 0
            
            for source, sentiment in sources.items():
                weight = weights.get(source, 0.1)
                weighted_sentiment += sentiment * weight
                total_weight += weight
            
            if total_weight == 0:
                return None
            
            final_sentiment = weighted_sentiment / total_weight
            confidence = min(len(sources) / 3.0, 1.0)  # Higher confidence with more sources
            
            sentiment_data = SentimentData(
                symbol=symbol,
                sentiment_score=final_sentiment,
                confidence=confidence,
                sources=sources,
                context={
                    'analysis_time': asyncio.get_event_loop().time(),
                    'sources_count': len(sources)
                }
            )
            
            # Cache the result
            self.cache[cache_key] = sentiment_data
            
            return sentiment_data
            
        except Exception as e:
            logger.warning("Sentiment analysis failed for %s: %s", symbol, e)
            return None


async def get_sentiment_signal(symbol: str) -> Optional[Dict[str, Any]]:
    """Get sentiment-based trading signal for a symbol."""
    if not settings.sentiment_enabled:
        return None
    
    try:
        async with SentimentAnalyzer() as analyzer:
            sentiment_data = await analyzer.analyze_sentiment(symbol)
            
            if not sentiment_data:
                return None
            
            # Generate signal based on sentiment
            if sentiment_data.sentiment_score >= settings.sentiment_threshold:
                return {
                    'side': 'LONG',
                    'confidence': sentiment_data.confidence,
                    'sentiment_score': sentiment_data.sentiment_score,
                    'sources': sentiment_data.sources,
                    'context': {
                        'strategy': 'social_sentiment',
                        'sentiment_score': sentiment_data.sentiment_score,
                        'confidence': sentiment_data.confidence,
                        'sources': list(sentiment_data.sources.keys())
                    }
                }
            elif sentiment_data.sentiment_score <= (1 - settings.sentiment_threshold):
                return {
                    'side': 'SHORT',
                    'confidence': sentiment_data.confidence,
                    'sentiment_score': sentiment_data.sentiment_score,
                    'sources': sentiment_data.sources,
                    'context': {
                        'strategy': 'social_sentiment',
                        'sentiment_score': sentiment_data.sentiment_score,
                        'confidence': sentiment_data.confidence,
                        'sources': list(sentiment_data.sources.keys())
                    }
                }
            
            return None
            
    except Exception as e:
        logger.warning("Sentiment signal generation failed for %s: %s", symbol, e)
        return None
