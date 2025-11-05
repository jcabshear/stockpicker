import asyncio
from typing import List
from datetime import datetime, date
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.data.live import StockDataStream
from alpaca.data.enums import DataFeed
from strategy import BaseStrategy, Position, Signal
from config import settings
from risk import check_drawdown


class LiveTrader:
    """Execute live trades based on strategy signals"""
    
    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        self.positions: dict[str, Position] = {}
        self.market_data: dict = {}
        self.allow_trading = settings.allow_trading
        
        # Risk limits
        self.max_position_size = settings.max_usd_per_order
        self.max_daily_loss = settings.max_daily_loss
        self.daily_pnl = 0.0
        self.last_reset_date = date.today()
        
        # Stats
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            print(f"⚠️ Could not check market status: {e}")
            return False
    
    async def sync_positions(self):
        """Sync positions from Alpaca on startup"""
        try:
            alpaca_positions = self.trading_client.get_all_positions()
            for pos in alpaca_positions:
                self.positions[pos.symbol] = Position(
                    symbol=pos.symbol,
                    shares=float(pos.qty),
                    entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    entry_time=datetime.now(),  # We don't have actual entry time
                    pnl=float(pos.unrealized_pl),
                    pnl_pct=float(pos.unrealized_plpc)
                )
            if alpaca_positions:
                print(f"📊 Synced {len(alpaca_positions)} existing positions")
        except Exception as e:
            print(f"⚠️ Failed to sync positions: {e}")
    
    async def submit_order(self, symbol: str, side: OrderSide, notional: float):
        """Submit market order and wait for fill"""
        if not self.allow_trading:
            print(f"💤 Trading disabled. Would {side.name} ${notional:.2f} of {symbol}")
            return None
        
        try:
            req = MarketOrderRequest(
                symbol=symbol,
                notional=notional,
                side=side,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.SIMPLE
            )
            order = self.trading_client.submit_order(req)
            print(f"📝 Order submitted: {side.name} ${notional:.2f} of {symbol}")
            
            # Wait for fill (with timeout)
            max_wait = 10
            for i in range(max_wait):
                await asyncio.sleep(1)
                order = self.trading_client.get_order_by_id(order.id)
                
                if order.status == 'filled':
                    self.total_trades += 1
                    print(f"✅ Order filled: {side.name} ${notional:.2f} of {symbol}")
                    return order
                elif order.status in ['cancelled', 'expired', 'rejected']:
                    print(f"❌ Order {order.status}: {symbol}")
                    return None
            
            print(f"⚠️ Order not filled after {max_wait}s, status: {order.status}")
            return None
            
        except Exception as e:
            print(f"❌ Order failed: {e}")
            return None
    
    def reset_daily_pnl_if_needed(self):
        """Reset daily PnL at the start of a new day"""
        current_date = date.today()
        if current_date != self.last_reset_date:
            print(f"\n{'='*80}")
            print(f"📅 New trading day: {current_date}")
            print(f"   Previous day P&L: ${self.daily_pnl:.2f}")
            print(f"{'='*80}\n")
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
    
    def check_risk_limits(self) -> bool:
        """Check if we're within risk limits"""
        return check_drawdown(self.daily_pnl, self.max_daily_loss)
    
    async def process_signals(self, signals: List[Signal]):
        """Process trading signals"""
        if not self.is_market_open():
            return
        
        if not self.check_risk_limits():
            return
        
        try:
            account = self.trading_client.get_account()
            account_value = float(account.equity)
            
            for signal in signals:
                if signal.action == 'buy' and signal.symbol not in self.positions:
                    # Calculate position size
                    size = self.strategy.get_position_size(
                        signal.symbol, 
                        account_value, 
                        signal.confidence
                    )
                    size = min(size, self.max_position_size)
                    
                    # Submit order
                    order = await self.submit_order(signal.symbol, OrderSide.BUY, size)
                    
                    if order and signal.symbol in self.market_data:
                        # Use actual fill price if available
                        fill_price = float(order.filled_avg_price) if order.filled_avg_price else self.market_data[signal.symbol]['close']
                        shares = size / fill_price
                        
                        self.positions[signal.symbol] = Position(
                            symbol=signal.symbol,
                            shares=shares,
                            entry_price=fill_price,
                            current_price=fill_price,
                            entry_time=datetime.now(),
                            pnl=0.0,
                            pnl_pct=0.0
                        )
                        print(f"📊 Position opened: {signal.symbol} @ ${fill_price:.2f} | {signal.reason}")
                
                elif signal.action == 'sell' and signal.symbol in self.positions:
                    # Close position
                    pos = self.positions[signal.symbol]
                    notional = pos.shares * pos.current_price
                    
                    order = await self.submit_order(signal.symbol, OrderSide.SELL, notional)
                    
                    if order:
                        # Use actual fill price
                        fill_price = float(order.filled_avg_price) if order.filled_avg_price else pos.current_price
                        final_pnl = (fill_price - pos.entry_price) * pos.shares
                        final_pnl_pct = (fill_price - pos.entry_price) / pos.entry_price
                        
                        self.daily_pnl += final_pnl
                        
                        if final_pnl > 0:
                            self.winning_trades += 1
                            print(f"💰 Position closed: {signal.symbol} @ ${fill_price:.2f} | Profit: ${final_pnl:.2f} ({final_pnl_pct*100:.2f}%)")
                        else:
                            self.losing_trades += 1
                            print(f"📉 Position closed: {signal.symbol} @ ${fill_price:.2f} | Loss: ${final_pnl:.2f} ({final_pnl_pct*100:.2f}%)")
                        
                        del self.positions[signal.symbol]
        
        except Exception as e:
            print(f"❌ Error processing signals: {e}")
    
    async def handle_bar(self, bar):
        """Handle incoming bar data"""
        # Reset daily PnL if new day
        self.reset_daily_pnl_if_needed()
        
        symbol = bar.symbol
        
        # Update market data
        self.market_data[symbol] = {
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        }
        
        # Update positions
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.current_price = bar.close
            pos.pnl = (bar.close - pos.entry_price) * pos.shares
            pos.pnl_pct = (bar.close - pos.entry_price) / pos.entry_price
            
            # Check exit
            if self.strategy.should_exit(pos, self.market_data):
                print(f"🛑 Exit signal for {symbol}: PnL {pos.pnl_pct*100:.2f}%")
                
                notional = pos.shares * bar.close
                order = await self.submit_order(symbol, OrderSide.SELL, notional)
                
                if order:
                    # Use actual fill price
                    fill_price = float(order.filled_avg_price) if order.filled_avg_price else bar.close
                    final_pnl = (fill_price - pos.entry_price) * pos.shares
                    
                    self.daily_pnl += final_pnl
                    
                    if final_pnl > 0:
                        self.winning_trades += 1
                        print(f"💰 Position closed: {symbol} | Profit: ${final_pnl:.2f}")
                    else:
                        self.losing_trades += 1
                        print(f"📉 Position closed: {symbol} | Loss: ${final_pnl:.2f}")
                    
                    del self.positions[symbol]
                return
        
        # Generate signals
        signals = self.strategy.generate_signals(self.market_data)
        
        if signals:
            print(f"📡 Generated {len(signals)} signals")
            await self.process_signals(signals)
    
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
        
        # Sync existing positions
        await self.sync_positions()
        
        feed_map = {"iex": DataFeed.IEX, "sip": DataFeed.SIP}
        feed = feed_map.get(settings.feed.lower(), DataFeed.IEX)
        
        retry_delay = 5
        max_retry_delay = 300  # 5 minutes
        retry_count = 0
        max_retries = 10  # Give up after 10 attempts
        
        while retry_count < max_retries:
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
                print(f"🔌 Connecting to Alpaca data stream (attempt {retry_count + 1}/{max_retries})...")
                
                # Reset retry count on successful connection
                retry_count = 0
                retry_delay = 5
                
                # FIXED: Properly await the stream
                await stream._run_forever()
            
            except KeyboardInterrupt:
                print("\n🛑 Shutting down gracefully...")
                break
            except ValueError as e:
                if "connection limit exceeded" in str(e):
                    retry_count += 1
                    print(f"\n{'='*80}")
                    print(f"❌ CONNECTION LIMIT EXCEEDED (attempt {retry_count}/{max_retries})")
                    print(f"{'='*80}")
                    print(f"💡 Alpaca allows only 1 WebSocket connection at a time.")
                    print(f"   You likely have another instance or session still connected.")
                    print(f"\n📋 To fix this:")
                    print(f"   1. Visit: https://app.alpaca.markets/paper/dashboard")
                    print(f"   2. Log out and log back in (forces disconnect)")
                    print(f"   3. Or wait 5-10 minutes for timeout")
                    print(f"   4. Then resume this service")
                    print(f"\n🔄 Will retry in {retry_delay} seconds...")
                    print(f"{'='*80}\n")
                    
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                else:
                    print(f"❌ Stream error: {e}")
                    break
            except Exception as e:
                print(f"❌ Stream error: {e}")
                print(f"🔄 Reconnecting in {retry_delay} seconds...")
                
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
                retry_count += 1
        
        if retry_count >= max_retries:
            print("\n" + "="*80)
            print("🚨 FATAL: Could not connect after maximum retries")
            print("="*80)
            print("❌ Unable to establish WebSocket connection to Alpaca")
            print("\n📋 Please:")
            print("   1. Go to https://app.alpaca.markets/")
            print("   2. Log out completely")
            print("   3. Wait 10 minutes")
            print("   4. Redeploy this service on Render")
            print("="*80 + "\n")