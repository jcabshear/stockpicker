"""
Fixed Backtester with proper authentication
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from strategy import BaseStrategy


class Backtester:
    """Backtest trading strategies on historical data"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, initial_capital: float = 10000):
        """
        Initialize backtester with proper authentication
        
        Args:
            api_key: Alpaca API key (defaults to ALPACA_KEY env var)
            api_secret: Alpaca API secret (defaults to ALPACA_SECRET env var)
            initial_capital: Starting capital
        """
        # Use provided keys or fall back to environment variables
        self.api_key = api_key or os.getenv('ALPACA_KEY')
        self.api_secret = api_secret or os.getenv('ALPACA_SECRET')
        
        # Validate credentials
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "You must supply a method of authentication when running backtests. "
                "Either pass api_key and api_secret to the constructor, or set "
                "ALPACA_KEY and ALPACA_SECRET environment variables."
            )
        
        # Initialize client with validated credentials
        self.client = StockHistoricalDataClient(self.api_key, self.api_secret)
        self.initial_capital = initial_capital
        self.results = {}
    
    def fetch_data(self, symbols: List[str], start_date: datetime, end_date: datetime) -> dict:
        """Fetch historical bar data"""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Minute,
                start=start_date,
                end=end_date
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            # Organize by symbol
            data = {}
            for symbol in symbols:
                try:
                    symbol_data = df.loc[symbol] if symbol in df.index.get_level_values('symbol') else pd.DataFrame()
                    data[symbol] = symbol_data
                except:
                    data[symbol] = pd.DataFrame()
            
            return data
        except Exception as e:
            print(f"Error fetching data: {e}")
            raise
    
    def run(self, strategy: BaseStrategy, symbols: List[str], 
            start_date: datetime, end_date: datetime) -> dict:
        """Run backtest"""
        print(f"\n{'='*80}")
        print(f"Running backtest: {strategy.name}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"{'='*80}\n")
        
        # Fetch data
        print("Fetching historical data...")
        data = self.fetch_data(symbols, start_date, end_date)
        
        # Initialize tracking
        cash = self.initial_capital
        positions = {}
        trades = []
        equity_curve = [self.initial_capital]
        
        # Simulate trading
        print("Simulating trades...")
        
        for symbol in symbols:
            symbol_df = data.get(symbol)
            if symbol_df is None or symbol_df.empty:
                print(f"⚠️ No data for {symbol}, skipping")
                continue
            
            print(f"Processing {symbol} ({len(symbol_df)} bars)...")
            
            for timestamp, bar in symbol_df.iterrows():
                # Update positions
                for sym, pos in positions.items():
                    if sym == symbol:
                        pos['current_price'] = bar['close']
                        pos['pnl'] = (bar['close'] - pos['entry_price']) * pos['shares']
                        pos['pnl_pct'] = (bar['close'] - pos['entry_price']) / pos['entry_price']
                
                # Generate signals
                market_data = {symbol: bar}
                signals = strategy.generate_signals(market_data)
                
                # Execute signals
                for signal in signals:
                    if signal.action == 'buy' and signal.symbol not in positions:
                        # Calculate position size (use 10% of capital per position)
                        position_size = min(cash * 0.1, self.initial_capital * 0.2)
                        shares = position_size / signal.price
                        cost = shares * signal.price
                        
                        if cost <= cash:
                            cash -= cost
                            positions[signal.symbol] = {
                                'shares': shares,
                                'entry_price': signal.price,
                                'current_price': signal.price,
                                'entry_time': timestamp,
                                'pnl': 0,
                                'pnl_pct': 0
                            }
                            trades.append({
                                'symbol': signal.symbol,
                                'action': 'buy',
                                'shares': shares,
                                'price': signal.price,
                                'timestamp': timestamp,
                                'reason': signal.reason,
                                'pnl': 0,
                                'pnl_pct': 0
                            })
                    
                    elif signal.action == 'sell' and signal.symbol in positions:
                        pos = positions[signal.symbol]
                        proceeds = pos['shares'] * signal.price
                        pnl = (signal.price - pos['entry_price']) * pos['shares']
                        pnl_pct = (signal.price - pos['entry_price']) / pos['entry_price']
                        
                        cash += proceeds
                        trades.append({
                            'symbol': signal.symbol,
                            'action': 'sell',
                            'shares': pos['shares'],
                            'price': signal.price,
                            'timestamp': timestamp,
                            'reason': signal.reason,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct
                        })
                        del positions[signal.symbol]
                
                # Calculate current equity
                position_value = sum(p['shares'] * p['current_price'] for p in positions.values())
                total_equity = cash + position_value
                equity_curve.append(total_equity)
        
        # Calculate metrics
        final_value = cash + sum(p['shares'] * p['current_price'] for p in positions.values())
        total_return = final_value - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # Trade statistics
        trades_df = pd.DataFrame(trades)
        sell_trades = trades_df[trades_df['action'] == 'sell']
        
        winning_trades = len(sell_trades[sell_trades['pnl'] > 0])
        losing_trades = len(sell_trades[sell_trades['pnl'] < 0])
        total_trades = len(sell_trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = sell_trades[sell_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = abs(sell_trades[sell_trades['pnl'] < 0]['pnl'].mean()) if losing_trades > 0 else 0
        
        # Profit factor
        total_wins = sell_trades[sell_trades['pnl'] > 0]['pnl'].sum() if winning_trades > 0 else 0
        total_losses = abs(sell_trades[sell_trades['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        returns = pd.Series(equity_curve).pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 0 and returns.std() > 0 else 0
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = equity_series - running_max
        max_drawdown = drawdown.min()
        max_drawdown_pct = (max_drawdown / running_max.max() * 100) if running_max.max() > 0 else 0
        
        # Store results
        self.results = {
            'strategy': strategy.name,
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'trades': trades_df,
            'equity_curve': equity_curve
        }
        
        return self.results
    
    def print_results(self):
        """Print formatted backtest results"""
        if not self.results:
            print("No results to display. Run backtest first.")
            return
        
        r = self.results
        
        print(f"\n{'='*80}")
        print("BACKTEST RESULTS")
        print(f"{'='*80}")
        print(f"Strategy: {r['strategy']}")
        print(f"\nCapital:")
        print(f"  Initial: ${r['initial_capital']:,.2f}")
        print(f"  Final: ${r['final_value']:,.2f}")
        print(f"  Return: ${r['total_return']:,.2f} ({r['total_return_pct']:+.2f}%)")
        print(f"\nTrades:")
        print(f"  Total: {r['total_trades']}")
        print(f"  Wins: {r['winning_trades']}")
        print(f"  Losses: {r['losing_trades']}")
        print(f"  Win Rate: {r['win_rate']*100:.1f}%")
        print(f"\nPerformance:")
        print(f"  Avg Win: ${r['avg_win']:.2f}")
        print(f"  Avg Loss: ${r['avg_loss']:.2f}")
        print(f"  Profit Factor: {r['profit_factor']:.2f}")
        print(f"  Sharpe Ratio: {r['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: ${r['max_drawdown']:.2f} ({r['max_drawdown_pct']:.2f}%)")
        print(f"{'='*80}\n")