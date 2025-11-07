"""
Integrated Backtester with Progress Tracking
Combines daily screening with intraday trading models
Each day: Screen → Select top N → Trade → Close by 3:40 PM

FIXED VERSION with progress callbacks
"""

import pandas as pd
from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Tuple, Callable, Optional
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from screening_models import get_screener
from daytrade_models import get_day_trade_model
from stock_universe import get_full_universe


class IntegratedBacktester:
    """Backtest with daily screening + intraday trading"""
    
    def __init__(self, api_key: str, api_secret: str, initial_capital: float = 10000):
        """
        Initialize backtester with API credentials
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            initial_capital: Starting capital for backtest
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.initial_capital = initial_capital
        self.feed = DataFeed.IEX
    
    def fetch_minute_data(self, symbols: List[str], date: datetime) -> Dict[str, pd.DataFrame]:
        """Fetch minute-level data for trading day"""
        start = datetime.combine(date.date(), dt_time(9, 30))
        end = datetime.combine(date.date(), dt_time(16, 0))
        
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Minute,
                start=start,
                end=end,
                feed=self.feed
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            # Organize by symbol
            minute_data = {}
            for symbol in symbols:
                try:
                    if symbol in df.index.get_level_values('symbol'):
                        minute_data[symbol] = df.loc[symbol]
                except:
                    continue
            
            return minute_data
        except Exception as e:
            print(f"Error fetching minute data for {date.date()}: {e}")
            return {}
    
    def simulate_trading_day(self, selected_stocks: List, date: datetime,  # 🔧 FIX: Changed List[dict] to List
                            day_model, cash: float, positions: dict, 
                            force_execution: bool) -> Tuple[float, dict, List[dict]]:
        """
        Simulate one trading day
        
        Returns:
            (ending_cash, ending_positions, trades)
        """
        trades = []
        
        # 🔧 FIX: Use attribute access instead of dictionary access
        symbols = [s.symbol for s in selected_stocks]
        minute_data = self.fetch_minute_data(symbols, date)
        
        if not minute_data:
            return cash, positions, trades
        
        # Get all unique timestamps
        all_timestamps = set()
        for symbol_df in minute_data.values():
            all_timestamps.update(symbol_df.index.tolist())
        
        trading_minutes = sorted(list(all_timestamps))
        
        for minute_ts in trading_minutes:
            current_time = minute_ts.to_pydatetime() if hasattr(minute_ts, 'to_pydatetime') else minute_ts
            
            # Close all positions at 3:40 PM
            if current_time.hour == 15 and current_time.minute >= 40:
                for symbol in list(positions.keys()):
                    pos = positions[symbol]
                    symbol_df = minute_data.get(symbol)
                    if symbol_df is not None and minute_ts in symbol_df.index:
                        current_bar = symbol_df.loc[minute_ts]
                        exit_price = current_bar['close']
                        
                        pnl = (exit_price - pos['entry_price']) * pos['shares']
                        cash += pos['shares'] * exit_price
                        
                        trades.append({
                            'symbol': symbol,
                            'action': 'sell',
                            'shares': pos['shares'],
                            'price': exit_price,
                            'timestamp': current_time,
                            'reason': 'End of day exit',
                            'pnl': pnl,
                            'pnl_pct': (exit_price - pos['entry_price']) / pos['entry_price']
                        })
                        
                        del positions[symbol]
                
                break  # End trading
            
            # Check exits for existing positions
            for symbol in list(positions.keys()):
                pos = positions[symbol]
                symbol_df = minute_data.get(symbol)
                
                if symbol_df is not None and minute_ts in symbol_df.index:
                    current_bar = symbol_df.loc[minute_ts].to_dict()
                    
                    should_exit, reason = day_model.should_exit(pos, current_bar, current_time)
                    
                    if should_exit:
                        exit_price = current_bar['close']
                        pnl = (exit_price - pos['entry_price']) * pos['shares']
                        cash += pos['shares'] * exit_price
                        
                        trades.append({
                            'symbol': symbol,
                            'action': 'sell',
                            'shares': pos['shares'],
                            'price': exit_price,
                            'timestamp': current_time,
                            'reason': reason,
                            'pnl': pnl,
                            'pnl_pct': (exit_price - pos['entry_price']) / pos['entry_price']
                        })
                        
                        del positions[symbol]
            
            # Look for new entries
            for stock in selected_stocks:
                symbol = stock.symbol  # 🔧 FIX: Use attribute access
                
                if symbol in positions:
                    continue
                
                symbol_df = minute_data.get(symbol)
                if symbol_df is None or minute_ts not in symbol_df.index:
                    continue
                
                minute_bars = symbol_df.loc[:minute_ts]
                signal = day_model.generate_signal(symbol, minute_bars, stock)
                
                if signal and signal.action == 'buy':
                    if not force_execution and signal.confidence < 0.7:
                        continue
                    
                    account_value = cash + sum(p['shares'] * p['current_price'] for p in positions.values())
                    position_size = min(account_value * 0.02, cash * 0.30)
                    
                    if position_size < 100:
                        continue
                    
                    shares = position_size / signal.price
                    cost = shares * signal.price
                    
                    if cost <= cash:
                        cash -= cost
                        
                        positions[symbol] = {
                            'symbol': symbol,
                            'shares': shares,
                            'entry_price': signal.price,
                            'current_price': signal.price,
                            'entry_time': current_time,
                            'stop_loss': signal.stop_loss,
                            'take_profit': signal.take_profit
                        }
                        
                        trades.append({
                            'symbol': symbol,
                            'action': 'buy',
                            'shares': shares,
                            'price': signal.price,
                            'timestamp': current_time,
                            'reason': signal.reason,
                            'pnl': 0,
                            'pnl_pct': 0
                        })
            
            # Update current prices
            for symbol, pos in positions.items():
                symbol_df = minute_data.get(symbol)
                if symbol_df is not None and minute_ts in symbol_df.index:
                    current_bar = symbol_df.loc[minute_ts]
                    pos['current_price'] = current_bar['close']
        
        return cash, positions, trades
    
    def run(self, screener_model: str, screener_params: dict,
            day_model: str, day_model_params: dict,
            start_date: datetime, end_date: datetime,
            stock_universe: List[str] = None,
            top_n: int = 3, min_score: float = 60,
            force_execution: bool = False,
            progress_callback: Optional[Callable] = None) -> dict:
        """
        Run integrated backtest with progress tracking
        
        Args:
            progress_callback: Optional function(message, progress_pct) for progress updates
        """
        if stock_universe is None:
            stock_universe = get_full_universe()
        
        # Count total trading days for progress
        total_days = 0
        temp_date = start_date
        while temp_date <= end_date:
            if temp_date.weekday() < 5:  # Weekday
                total_days += 1
            temp_date += timedelta(days=1)
        
        if progress_callback:
            progress_callback("Initializing backtest...", 0)
        
        print(f"\n{'='*80}")
        print("INTEGRATED BACKTEST")
        print(f"{'='*80}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Universe: {len(stock_universe)} stocks")
        print(f"Screener: {screener_model}")
        print(f"Day Model: {day_model}")
        print(f"Top N: {top_n} stocks per day")
        print(f"Min Score: {min_score}")
        print(f"Force Execution: {force_execution}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"{'='*80}\n")
        
        # Initialize
        cash = self.initial_capital
        positions = {}
        all_trades = []
        daily_results = []
        
        # Create models
        screener = get_screener(screener_model, self.api_key, self.api_secret, **screener_params)
        day_trader = get_day_trade_model(day_model, **day_model_params)
        
        # Iterate through trading days
        current_date = start_date
        day_count = 0
        completed_days = 0
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            day_count += 1
            completed_days += 1
            progress_pct = int((completed_days / total_days) * 100)
            
            day_str = current_date.strftime("%Y-%m-%d")
            
            if progress_callback:
                progress_callback(f"Day {day_count}: Screening {len(stock_universe)} stocks...", progress_pct)
            
            print(f"\n{'='*80}")
            print(f"DAY {day_count}: {day_str}")
            print(f"{'='*80}")
            print(f"Starting cash: ${cash:,.2f}")
            
            # Step 1: Screen stocks
            print(f"\n🔍 Screening {len(stock_universe)} stocks...")
            screener.client = self.client
            screened = screener.screen(stock_universe, min_score=min_score)
            
            if not screened:
                print(f"❌ No stocks passed screening (min score: {min_score})")
                current_date += timedelta(days=1)
                continue
            
            # Select top N
            selected = screened[:top_n]
            
            print(f"\n✅ {len(screened)} stocks qualified, selected top {top_n}:")
            for i, stock in enumerate(selected, 1):
                print(f"  {i}. {stock.symbol}: {stock.score:.1f} - {stock.reason}")
            
            # Step 2: Simulate trading day
            if progress_callback:
                symbols_str = ", ".join([s.symbol for s in selected])
                progress_callback(f"Day {day_count}: Trading {symbols_str}...", progress_pct)
            
            print(f"\n💹 Simulating trading day...")
            
            cash, positions, day_trades = self.simulate_trading_day(
                selected,
                current_date,
                day_trader,
                cash,
                positions,
                force_execution
            )
            
            # Track results
            all_trades.extend(day_trades)
            
            # Calculate day P&L
            buy_trades = [t for t in day_trades if t['action'] == 'buy']
            sell_trades = [t for t in day_trades if t['action'] == 'sell']
            day_pnl = sum(t['pnl'] for t in sell_trades)
            
            print(f"\n📊 Day Summary:")
            print(f"   Entries: {len(buy_trades)}")
            print(f"   Exits: {len(sell_trades)}")
            print(f"   Day P&L: ${day_pnl:,.2f}")
            print(f"   Ending cash: ${cash:,.2f}")
            print(f"   Open positions: {len(positions)}")
            
            daily_results.append({
                'date': current_date.date(),
                'screened': len(screened),
                'selected': [s.symbol for s in selected],
                'entries': len(buy_trades),
                'exits': len(sell_trades),
                'day_pnl': day_pnl,
                'ending_cash': cash,
                'open_positions': len(positions)
            })
            
            current_date += timedelta(days=1)
        
        # Final calculations
        if progress_callback:
            progress_callback("Calculating final results...", 95)
        
        print(f"\n{'='*80}")
        print("FINAL RESULTS")
        print(f"{'='*80}")
        
        # Close remaining positions
        if positions:
            print(f"\nClosing {len(positions)} remaining positions...")
            for symbol, pos in positions.items():
                cash += pos['shares'] * pos['current_price']
        
        final_value = cash
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Trade statistics
        trades_df = pd.DataFrame(all_trades)
        close_trades = trades_df[trades_df['action'] == 'sell'] if len(trades_df) > 0 else pd.DataFrame()
        
        if len(close_trades) > 0:
            winning_trades = close_trades[close_trades['pnl'] > 0]
            losing_trades = close_trades[close_trades['pnl'] < 0]
            
            win_rate = len(winning_trades) / len(close_trades)
            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        # Count unique stocks traded
        unique_stocks = set()
        for trade in all_trades:
            if trade['action'] == 'buy':
                unique_stocks.add(trade['symbol'])
        
        results = {
            'strategy': f"{screener_model} + {day_model}",
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_trades': len(close_trades),
            'winning_trades': len(winning_trades) if len(close_trades) > 0 else 0,
            'losing_trades': len(losing_trades) if len(close_trades) > 0 else 0,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'trades': all_trades,
            'daily_results': daily_results,
            'unique_stocks_traded': len(unique_stocks),
            'screening_sessions': len(daily_results)
        }
        
        if progress_callback:
            progress_callback("Backtest complete!", 100)
        
        print(f"\nInitial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return*100:.2f}%")
        print(f"\nTotal Trades: {len(close_trades)}")
        print(f"Win Rate: {win_rate*100:.1f}%")
        print(f"Profit Factor: {profit_factor:.2f}")
        print(f"\nUnique Stocks Traded: {len(unique_stocks)}")
        print(f"Screening Sessions: {len(daily_results)}")
        print(f"{'='*80}\n")
        
        return results