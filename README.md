# Alpaca Trading Bot on Render

A modular 24x7 autonomous trading bot that runs on Render. Uses separate components for strategy, trading, and backtesting.

## Architecture

```
├── main.py                      # Entry point & API server
├── sma_crossover_strategy.py   # SMA Crossover strategy implementation
├── live_trader.py               # Live trading execution engine
├── strategy.py                  # Base strategy classes
├── backtester.py                # Historical backtesting
├── config.py                    # Configuration management
├── risk.py                      # Risk management
├── requirements.txt             # Python dependencies
└── render.yaml                  # Render deployment config
```

## Features

- ✅ **Modular Design**: Separate strategy, trader, and backtest components
- ✅ **Live Trading**: Real-time data streaming from Alpaca
- ✅ **Paper Trading**: Safe testing with simulated money
- ✅ **Risk Management**: Stop-loss and daily loss limits
- ✅ **RESTful API**: Monitor bot via HTTP endpoints
- ✅ **Backtesting**: Test strategies on historical data
- ✅ **24/7 Operation**: Runs continuously on Render

## Strategy

**SMA Crossover with Volume Confirmation**
- Short SMA (default: 5 periods) crosses Long SMA (default: 20 periods)
- Entry requires volume > 1.5x average
- Exit on opposite crossover or 2% stop-loss
- Position sizing: 1-2% of account per trade

## Quick Start

### 1. Deploy to Render

1. Push this repo to GitHub
2. Create a new **Background Worker** in Render
3. Connect your GitHub repository
4. Render will use `render.yaml` for configuration

### 2. Set Environment Variables

In Render Dashboard, add these **Secret Files** or **Environment Variables**:

**Required:**
```
ALPACA_KEY=your_alpaca_api_key
ALPACA_SECRET=your_alpaca_secret_key
```

**Optional (with defaults):**
```
PAPER=true                    # Use paper trading (true/false)
ALLOW_TRADING=false           # Enable actual trading (true/false)
MAX_USD_PER_ORDER=100        # Max position size in USD
MAX_DAILY_LOSS=50            # Max daily loss in USD
FEED=iex                     # Data feed (iex/sip)
SYMBOLS=AAPL,MSFT,GOOGL     # Comma-separated symbols
SHORT_WINDOW=5               # Short SMA window
LONG_WINDOW=20               # Long SMA window
VOLUME_THRESHOLD=1.5         # Volume multiplier for entry
STOP_LOSS_PCT=0.02          # Stop loss percentage (0.02 = 2%)
```

### 3. Deploy

Render will automatically:
1. Install dependencies from `requirements.txt`
2. Start the bot with `python main.py`
3. Run the FastAPI server on port 10000

### 4. Monitor

**Health Check:**
```bash
curl https://your-app.onrender.com/health
```

**View Positions:**
```bash
curl https://your-app.onrender.com/positions
```

**Trading Stats:**
```bash
curl https://your-app.onrender.com/stats
```

**Emergency Stop:**
```bash
curl -X POST "https://your-app.onrender.com/kill?token=let-me-in"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Bot status and basic metrics |
| `/positions` | GET | Current open positions |
| `/stats` | GET | Trading statistics |
| `/kill?token=let-me-in` | POST | Emergency stop (disables trading) |

## Local Development

### Setup

```bash
# Clone repository
git clone <your-repo-url>
cd trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ALPACA_KEY="your_key"
export ALPACA_SECRET="your_secret"
export PAPER="true"
export ALLOW_TRADING="false"
```

### Run Locally

```bash
python main.py
```

Visit `http://localhost:10000` to see the API.

### Backtest a Strategy

```python
from datetime import datetime, timedelta
from backtester import Backtester
from sma_crossover_strategy import SMACrossoverStrategy

# Initialize
backtester = Backtester(
    api_key="your_key",
    api_secret="your_secret",
    initial_capital=10000
)

# Create strategy
strategy = SMACrossoverStrategy(
    short_window=5,
    long_window=20,
    volume_threshold=1.5,
    stop_loss_pct=0.02
)

# Run backtest
results = backtester.run(
    strategy=strategy,
    symbols=['AAPL', 'MSFT'],
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

# Print results
backtester.print_results()
```

## Safety & Best Practices

### Before Going Live

- [ ] **Test with paper trading** for at least 1 week
- [ ] **Run backtests** on historical data
- [ ] **Start with ALLOW_TRADING=false** to test monitoring
- [ ] **Use small position sizes** initially
- [ ] **Set tight loss limits** when starting
- [ ] **Monitor continuously** for first few days

### Risk Management

1. **Always start with paper trading** (`PAPER=true`)
2. **Test monitoring first** (`ALLOW_TRADING=false`)
3. **Use small position sizes** (`MAX_USD_PER_ORDER=50` or less)
4. **Set daily loss limits** (`MAX_DAILY_LOSS=20` or less)
5. **Monitor the `/health` endpoint** with external tools
6. **Have the kill switch ready** (`/kill?token=let-me-in`)

### Production Checklist

- [ ] Alpaca API keys are set as **Secret Files** in Render
- [ ] `PAPER=true` initially
- [ ] `ALLOW_TRADING=false` for monitoring test
- [ ] Position sizes are reasonable for account size
- [ ] Daily loss limit is set conservatively
- [ ] External monitoring (UptimeRobot, etc.) configured
- [ ] Backtest results are satisfactory
- [ ] Emergency stop tested and working

## Customization

### Create a New Strategy

```python
from strategy import BaseStrategy, Signal, Position
from typing import List
from datetime import datetime

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My Strategy")
    
    def generate_signals(self, market_data: dict) -> List[Signal]:
        signals = []
        # Your logic here
        return signals
    
    def should_exit(self, position: Position, current_data: dict) -> bool:
        # Your exit logic here
        return False
```

Then use it in `main.py`:
```python
from my_strategy import MyStrategy

strategy = MyStrategy()
trader = LiveTrader(strategy)
```

## Troubleshooting

### Bot Not Starting
- Check Render logs for errors
- Verify `ALPACA_KEY` and `ALPACA_SECRET` are set
- Ensure all dependencies installed correctly

### No Trades Being Made
- Check `ALLOW_TRADING` is set to `true`
- Verify symbols are valid and have data
- Check `/health` endpoint shows "trading_enabled": true
- Review logs for strategy signals

### Connection Errors
- Check Alpaca API status
- Verify API keys are valid
- Ensure data feed (`FEED`) is correct for your account

## Warning

⚠️ **TRADING INVOLVES RISK OF LOSS**

This bot is for educational purposes. Always:
- Test thoroughly with paper trading
- Start with small amounts
- Monitor continuously
- Understand the strategy before using
- Never risk more than you can afford to lose

Past performance does not guarantee future results.

## License

MIT License - Use at your own risk.

## Support

For issues:
1. Check Render logs
2. Review `/health` endpoint
3. Test with paper trading first
4. Verify all environment variables