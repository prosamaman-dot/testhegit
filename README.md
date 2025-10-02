# Scalper Bot - Professional Trading Bot

A high-performance cryptocurrency scalping bot with advanced signal generation and risk management.

## 🚀 Features

- **Multiple Trading Strategies**: Triple EMA, Bollinger Bands Squeeze, Breakout Retest, and more
- **Advanced Risk Management**: Dynamic stop-loss and take-profit calculation
- **Real-time Alerts**: Telegram notifications for all trading signals
- **Multi-Exchange Support**: Bybit, Binance, MEXC, OKX
- **Professional Architecture**: Clean, modular codebase
- **High-Quality Signals**: Selective filtering for 10/10 opportunities only

## 📁 Project Structure

```
scalper-bot/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── src/                   # Source code
│   ├── __init__.py
│   ├── config/            # Configuration
│   │   ├── __init__.py
│   │   └── settings.py    # Bot settings
│   ├── core/              # Core bot logic
│   │   ├── __init__.py
│   │   ├── bot.py         # Main bot class
│   │   ├── performance.py # Performance tracking
│   │   └── risk_manager.py # Risk management
│   ├── data/              # Data fetching
│   │   ├── __init__.py
│   │   ├── fetcher.py     # Market data fetcher
│   │   └── mock_fetcher.py # Mock data for testing
│   ├── strategies/        # Trading strategies
│   │   ├── __init__.py
│   │   ├── signal_generator.py # Signal generation
│   │   ├── indicators.py  # Technical indicators
│   │   ├── volume_strategies.py # Volume-based strategies
│   │   └── sentiment_analysis.py # Sentiment analysis
│   ├── notifications/     # Alert system
│   │   ├── __init__.py
│   │   └── telegram.py    # Telegram notifications
│   └── utils/             # Utilities
│       ├── __init__.py
│       ├── logger.py      # Logging system
│       └── simple_logger.py # Simple logging
├── logs/                  # Log files
├── data/                  # Data storage
└── venv/                  # Virtual environment
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd scalper-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure settings**
   - Edit `src/config/settings.py` to configure your trading parameters
   - Set your Telegram bot token and chat ID
   - Choose your exchange and trading symbols

## 🚀 Usage

### Basic Usage

```bash
python main.py
```

### Configuration

The bot can be configured through environment variables or by editing `src/config/settings.py`:

```python
# Key settings
EXCHANGE = "bybit"  # or "binance", "mexc", "okx"
SYMBOLS = "BTC/USDT,ETH/USDT,SOL/USDT"  # Trading pairs
TARGET_RR = "3.0"  # Risk/Reward ratio
ACTIVE_STRATEGIES = "triple_ema,bb_squeeze,breakout_retest"
```

### Telegram Setup

1. Create a Telegram bot with @BotFather
2. Get your bot token
3. Get your chat ID
4. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   ```

## 📊 Trading Strategies

### Available Strategies

1. **Triple EMA** - Trend following with pullback entries
2. **Bollinger Bands Squeeze** - Volatility breakout detection
3. **Breakout Retest** - Support/resistance breakout confirmation
4. **VWAP Fade** - Mean reversion around VWAP
5. **Fast MACD** - Momentum-based signals
6. **Range Scalp** - Range-bound trading
7. **Keltner + Stochastic** - Trend + momentum combination
8. **VWAP + EMA Confluence** - Multi-indicator confirmation

### Signal Quality Filters

- **Risk/Reward Ratio**: Minimum 3:1
- **Volatility Filter**: Minimum 0.25% ATR
- **Cooldown Periods**: 3 minutes between signals
- **MACD Strength**: Requires strong momentum signals

## 📈 Performance Tracking

The bot tracks:
- Win/Loss ratio
- Average profit per trade
- Total P&L
- Strategy performance
- Risk metrics

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Adding New Strategies

1. Create strategy function in `src/strategies/indicators.py`
2. Add strategy to `SignalGenerator` class
3. Update `ACTIVE_STRATEGIES` in config

## 📝 Logging

Logs are stored in:
- `logs/bot.log` - Main bot logs
- `logs/performance.log` - Performance metrics
- `logs/errors.log` - Error logs

## ⚠️ Risk Disclaimer

This bot is for educational purposes only. Trading cryptocurrencies involves substantial risk of loss. Never trade with money you cannot afford to lose.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the logs for troubleshooting