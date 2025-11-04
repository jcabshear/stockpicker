"""
Simple All-in-One Autonomous Trading Bot
Combines strategy, live trading, and monitoring in one file
"""

import asyncio
from collections import deque
from statistics import fmean
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

from fastapi import FastAPI, HTTPException
import uvicorn

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import TimeInForce, OrderSide, OrderClass
from alpaca.data.live import StockDataStream
from alpaca.data.enums import DataFeed

from config import settings
from risk import check_drawdown


# ============================================================================
# STRATEGY CLASSES
# ============================================================================

@dataclass
class Position:
    """Current position"""
    symbol: str
    shares: float
    entry_price: float
    current_price: float
    entry_time: datetime
    pnl: float = 0.0
    pnl_pct: float = 0.0


class SMACrossoverStrategy:
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, short_window: int = 5, long_window: int = 20, 
                 volume_threshold: float = 1.5, stop_loss_pct: float = 0.02):
        self.name = "SMA_Crossover"
        self.short_window = short_window
        self.long_window = long_window
        self.volume_threshold = volume_threshold
        self.stop_loss_pct = stop_loss_pct
        
        # Store price history
        self.price_history: dict[str, deque] = {}
        self.volume_history: dict[str, deque] = {}
        self.last_signal: dict[str, str] = {}
    
    def update_data(self, symbol: str, close_price: float, volume: float):
        """Update price and volume history"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.long_window)
            self.volume_history[symbol] = deque(maxlen=20)
        
        self.price_history[symbol].append(close_price)
        self.volume_history[symbol].append(volume)
    
    def generate_signal(self, symbol: str) -> Optional[str]:
        """Generate buy/sell signal for a symbol"""
        if symbol not in self.price_history:
            return None
        
        # Need enough data
        if len(self.price_history[symbol]) < self.long_window:
            return None
        
        # Calculate SMAs
        prices = list(self.price_history[symbol])
        short_sma = fmean(prices[-self.short_window:])
        long_sma = fmean(prices)
        
        # Calculate volume ratio
        volumes = list(self.volume_history[symbol])
        avg_volume = fmean(volumes) if len(volumes) > 0 else 1
        current_volume = volumes[-1] if len(volumes) > 0 else 0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Generate signal
        current_signal = None
        
        # Bullish crossover
        if short_sma > long_sma and self.last_signal.get(symbol) != 'buy':
            if volume_ratio > self.volume_threshold:
                current_signal = 'buy'
                print(f"📈 {symbol}: Bullish signal (SMA cross + {volume_ratio:.1f}x volume)")
        
        # Bearish crossover
        elif short_sma < long_sma and self.last_signal.get(symbol) != 'sell':
            if volume_ratio > self.volume_threshold:
                current_signal = 'sell'
                print(f"📉 {symbol}: Bearish signal (SMA cross + {volume_ratio:.1f}x volume)")
        
        if current_signal:
            self.last_signal[symbol] = current_signal
        
        return current_signal
    
    def should_exit(self, position: Position) -> bool:
        """Check if we should exit a position"""
        # Stop loss
        if position.pnl_pct <= -self.stop_loss_pct:
            print(f"🛑 {position.symbol}: Stop loss hit ({position.pnl_pct*100:.2f}%)")
            return True
        
        # Check for opposite signal
        symbol = position.symbol
        if symbol in self.price_history and len(self.price_history[symbol]) >= self.long_window:
            prices = list(self.price_history[symbol])
            short_sma = fmean(prices[-self.short_window:])
            long_sma = fmean(prices)
            
            # Exit long on bearish cross
            if position.shares > 0 and short_sma < long_sma:
                print(f"↩️  {symbol}: Exit long on bearish crossover")
                return True
            
            # Exit short on bullish cross
            if position.shares < 0 and short_sma > long_sma:
                print(f"↩️  {symbol}: Exit short on bullish crossover")
                return True
        
        return False


# ============================================================================
# LIVE TRADER
# ============================================================================

class LiveTrader:
    """Execute live trades based on strategy signals"""
    
    def __init__(self, strategy: SMACrossoverStrategy):
        self.strategy = strategy
        self.trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        self.positions: dict[str, Position] = {}
        self.allow_trading = settings.allow_trading
        
        # Risk limits
        self.max_position_size = settings.max_usd_per_order
        self.max_daily_loss = settings.max_daily_loss
        self.daily_pnl = 0.0
        
        # Stats
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
    
    async def submit_order(self, symbol: str, side: OrderSide, notional: float):
        """Submit market order"""
        if not self.allow_trading:
            print(f"💤 Trading disabled. Would {side.name} ${notional:.2f} of {symbol}")
            return None
        
        try:
            req = MarketOrderRequest(
                symbol=symbol,
                notional=notional,
                side=side,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.Simple
            )
            order = self.trading_client.submit_order(req)
            print(f"✅ Order submitted: {side.name} ${notional:.2f} of {symbol}")
            self.total_trades += 1
            return order
        except Exception as e:
            print(f"❌ Order failed: {e}")
            return None
    
    def check_risk_limits(self) -> bool:
        """Check if we're within risk limits"""
        if self.daily_pnl <= -self.max_daily_loss:
            print(f"⚠️  Daily loss limit reached: ${self.daily_pnl:.2f}")
            return False
        return True
    
    def handle_bar(self, bar):
        """Handle incoming bar data"""
        symbol = bar.symbol
        
        # Update strategy data
        self.strategy.update_data(symbol, bar.close, bar.volume)
        
        # Update existing positions
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.current_price = bar.close
            pos.pnl = (bar.close - pos.entry_price) * pos.shares
            pos.pnl_pct = (bar.close - pos.entry_price) / pos.entry_price
            
            # Check exit
            if self.strategy.should_exit(pos):
                asyncio.create_task(self._close_position(symbol, bar.close))
                return
        
        # Check risk limits
        if not check_drawdown(self.daily_pnl, self.max_daily_loss):
            return
        
        # Generate signal
        signal = self.strategy.generate_signal(symbol)
        
        if signal == 'buy' and symbol not in self.positions:
            asyncio.create_task(self._open_position(symbol, bar.close))
        elif signal == 'sell' and symbol in self.positions:
            asyncio.create_task(self._close_position(symbol, bar.close))
    
    async def _open_position(self, symbol: str, price: float):
        """Open a new position"""
        try:
            account = self.trading_client.get_account()
            account_value = float(account.equity)
            
            # Calculate position size (1-2% of account)
            size = min(account_value * 0.02, self.max_position_size)
            
            # Submit order
            order = await self.submit_order(symbol, OrderSide.BUY, size)
            
            if order:
                shares = size / price
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=shares,
                    entry_price=price,
                    current_price=price,
                    entry_time=datetime.now()
                )
                print(f"📊 Position opened: {symbol} @ ${price:.2f} ({shares:.2f} shares)")
        
        except Exception as e:
            print(f"Error opening position: {e}")
    
    async def _close_position(self, symbol: str, price: float):
        """Close an existing position"""
        if symbol not in self.positions:
            return
        
        try:
            pos = self.positions[symbol]
            notional = pos.shares * price
            
            order = await self.submit_order(symbol, OrderSide.SELL, notional)
            
            if order:
                self.daily_pnl += pos.pnl
                
                if pos.pnl > 0:
                    self.winning_trades += 1
                    print(f"💰 Position closed: {symbol} @ ${price:.2f} | Profit: ${pos.pnl:.2f} ({pos.pnl_pct*100:.2f}%)")
                else:
                    self.losing_trades += 1
                    print(f"📉 Position closed: {symbol} @ ${price:.2f} | Loss: ${pos.pnl:.2f} ({pos.pnl_pct*100:.2f}%)")
                
                del self.positions[symbol]
        
        except Exception as e:
            print(f"Error closing position: {e}")
    
    async def run(self, symbols: List[str]):
        """Start live trading"""
        print("\n" + "="*80)
        print(f"🤖 Starting {self.strategy.name} Trading Bot")
        print("="*80)
        print(f"Mode: {'PAPER' if settings.paper else 'LIVE'} Trading")
        print(f"Trading: {'ENABLED' if self.allow_trading else 'DISABLED'}")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Max Position Size: ${self.max_position_size}")
        print(f"Max Daily Loss: ${self.max_daily_loss}")
        print("="*80 + "\n")
        
        feed_map = {"iex": DataFeed.IEX, "sip": DataFeed.SIP}
        feed = feed_map.get(settings.feed.lower(), DataFeed.IEX)
        
        while True:
            try:
                stream = StockDataStream(
                    settings.alpaca_key,
                    settings.alpaca_secret,
                    feed=feed
                )
                
                # Subscribe to all symbols
                for symbol in symbols:
                    stream.subscribe_bars(self.handle_bar, symbol.strip())
                
                print(f"📡 Subscribed to {len(symbols)} symbols on {feed.name}")
                await stream.run()
            
            except Exception as e:
                print(f"❌ Stream error: {e}")
                await asyncio.sleep(5)


# ============================================================================
# FASTAPI APP FOR MONITORING
# ============================================================================

app = FastAPI()
trader: Optional[LiveTrader] = None

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "running",
        "trading_enabled": trader.allow_trading if trader else False,
        "daily_pnl": trader.daily_pnl if trader else 0,
        "positions": len(trader.positions) if trader else 0,
        "total_trades": trader.total_trades if trader else 0
    }

@app.get("/positions")
def get_positions():
    """Get current positions"""
    if not trader:
        return {"positions": []}
    
    return {
        "positions": [
            {
                "symbol": p.symbol,
                "shares": p.shares,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "pnl": p.pnl,
                "pnl_pct": p.pnl_pct * 100
            }
            for p in trader.positions.values()
        ]
    }

@app.get("/stats")
def get_stats():
    """Get trading stats"""
    if not trader:
        return {}
    
    win_rate = (trader.winning_trades / trader.total_trades * 100) if trader.total_trades > 0 else 0
    
    return {
        "total_trades": trader.total_trades,
        "winning_trades": trader.winning_trades,
        "losing_trades": trader.losing_trades,
        "win_rate": win_rate,
        "daily_pnl": trader.daily_pnl
    }

@app.post("/kill")
def kill(token: str):
    """Emergency stop"""
    if token != "let-me-in":
        raise HTTPException(status_code=401, detail="bad token")
    
    if trader:
        trader.allow_trading = False
    
    return {"ok": True, "message": "Trading disabled"}


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def run_http():
    """Run FastAPI server"""
    config = uvicorn.Config(app, host="0.0.0.0", port=10000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def heartbeat():
    """Periodic heartbeat"""
    while True:
        if trader:
            print(f"💓 Bot alive | Positions: {len(trader.positions)} | Daily P&L: ${trader.daily_pnl:.2f}")
        await asyncio.sleep(60)

async def main():
    global trader
    
    # Define symbols to trade
    symbols = getattr(settings, 'symbols', ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'])
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(',')]
    
    # Create strategy and trader
    strategy = SMACrossoverStrategy(
        short_window=settings.short_window if hasattr(settings, 'short_window') else 5,
        long_window=settings.long_window if hasattr(settings, 'long_window') else 20,
        volume_threshold=1.5,
        stop_loss_pct=0.02
    )
    
    trader = LiveTrader(strategy)
    
    # Run everything together
    await asyncio.gather(
        run_http(),
        trader.run(symbols),
        heartbeat()
    )

if __name__ == "__main__":
    asyncio.run(main())