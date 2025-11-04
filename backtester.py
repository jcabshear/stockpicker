import pandas as pd
from datetime import datetime, timedelta
from typing import List
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from strategy import BaseStrategy, Position


class Backtester:
    """Backtest trading strategies"""
    
    def __init__(self, api_key: str, api_secret: str, initial_capital: float = 100000):
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.initial_capital = initial_capital
        self.results = None
    
    def fetch_data(self, symbols: List[str], start_date: datetime, 
                   end_date: datetime, timeframe: TimeFrame = TimeFrame.Minute) -> pd.DataFrame:
        """Fetch historical data"""
        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=timeframe,
            start=start_date,
            end=end_date
        )
        
        bars = self.client.get_stock_bars(request)
        return bars.df
    
    def run(self, strategy: BaseStrategy, symbols: List[str], 
            start_date: datetime, end_date: datetime) -> dict:
        """
        Run backtest
        
        Returns:
            Dict with performance metrics
        """
        print(f"Backtesting {strategy.name} from {start_date} to {end_date}")
        
        # Fetch data
        df = self.fetch_data(symbols, start_date, end_date, TimeFrame.Minute)
        
        # Initialize
        cash = self.initial_capital
        positions = {}
        trades = []
        equity_curve = []
        
        # Group by timestamp and iterate
        for timestamp, group in df.groupby(level='timestamp'):
            # Prepare market data
            market_data = {}
            for symbol in symbols:
                if symbol in group.index.get_level_values('symbol'):
                    row = group.loc[(timestamp, symbol)]
                    market_data[symbol] = {
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['volume']
                    }
            
            # Update existing positions
            for symbol, pos in list(positions.items()):
                if symbol in market_data:
                    current_price = market_data[symbol]['close']
                    pos.current_price = current_price
                    pos.pnl = (current_price - pos.entry_price) * pos.shares
                    pos.pnl_pct = (current_price - pos.entry_price) / pos.entry_price
                    
                    # Check exit conditions
                    if strategy.should_exit(pos, market_data):
                        # Close position
                        cash += pos.shares * current_price
                        trades.append({
                            'symbol': symbol,
                            'action': 'close',
                            'shares': pos.shares,
                            'price': current_price,
                            'pnl': pos.pnl,
                            'pnl_pct': pos.pnl_pct,
                            'timestamp': timestamp
                        })
                        del positions[symbol]
            
            # Generate signals
            signals = strategy.generate_signals(market_data)
            
            # Execute signals
            for signal in signals:
                if signal.action == 'buy' and signal.symbol not in positions:
                    # Calculate position size
                    account_value = cash + sum(p.shares * p.current_price for p in positions.values())
                    size = strategy.get_position_size(signal.symbol, account_value, signal.confidence)
                    
                    # Open position
                    if size <= cash and signal.symbol in market_data:
                        price = market_data[signal.symbol]['close']
                        shares = size / price
                        
                        positions[signal.symbol] = Position(
                            symbol=signal.symbol,
                            shares=shares,
                            entry_price=price,
                            current_price=price,
                            entry_time=timestamp,
                            pnl=0.0,
                            pnl_pct=0.0
                        )
                        
                        cash -= size
                        trades.append({
                            'symbol': signal.symbol,
                            'action': 'open',
                            'shares': shares,
                            'price': price,
                            'pnl': 0,
                            'pnl_pct': 0,
                            'timestamp': timestamp
                        })
                
                elif signal.action == 'sell' and signal.symbol in positions:
                    # Close position
                    pos = positions[signal.symbol]
                    price = market_data[signal.symbol]['close']
                    cash += pos.shares * price
                    
                    trades.append({
                        'symbol': signal.symbol,
                        'action': 'close',
                        'shares': pos.shares,
                        'price': price,
                        'pnl': pos.pnl,
                        'pnl_pct': pos.pnl_pct,
                        'timestamp': timestamp
                    })
                    del positions[signal.symbol]
            
            # Track equity
            account_value = cash + sum(p.shares * p.current_price for p in positions.values())
            equity_curve.append({
                'timestamp': timestamp,
                'equity': account_value,
                'cash': cash,
                'positions_value': account_value - cash
            })
        
        # Calculate metrics
        trades_df = pd.DataFrame(trades)
        equity_df = pd.DataFrame(equity_curve)
        
        final_value = equity_df['equity'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        winning_trades = trades_df[trades_df['pnl'] > 0] if len(trades_df) > 0 else pd.DataFrame()
        losing_trades = trades_df[trades_df['pnl'] < 0] if len(trades_df) > 0 else pd.DataFrame()
        
        win_rate = len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0
        
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        
        # Sharpe ratio (simplified)
        returns = equity_df['equity'].pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * (252 ** 0.5) if len(returns) > 0 else 0
        
        # Max drawdown
        cummax = equity_df['equity'].cummax()
        drawdown = (equity_df['equity'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        self.results = {
            'strategy': strategy.name,
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_trades': len(trades_df),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'trades': trades_df,
            'equity_curve': equity_df
        }
        
        return self.results
    
    def print_results(self):
        """Print backtest results"""
        if not self.results:
            print("No results to display. Run backtest first.")
            return
        
        r = self.results
        print("\n" + "="*80)
        print(f"BACKTEST RESULTS: {r['strategy']}")
        print("="*80)
        print(f"Initial Capital:    ${r['initial_capital']:,.2f}")
        print(f"Final Value:        ${r['final_value']:,.2f}")
        print(f"Total Return:       {r['total_return_pct']:.2f}%")
        print(f"\nTotal Trades:       {r['total_trades']}")
        print(f"Winning Trades:     {r['winning_trades']} ({r['win_rate']*100:.1f}%)")
        print(f"Losing Trades:      {r['losing_trades']}")
        print(f"\nAvg Win:            ${r['avg_win']:,.2f}")
        print(f"Avg Loss:           ${r['avg_loss']:,.2f}")
        print(f"Profit Factor:      {r['profit_factor']:.2f}")
        print(f"\nSharpe Ratio:       {r['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:       {r['max_drawdown_pct']:.2f}%")
        print("="*80)