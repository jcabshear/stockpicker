"""
Backtest Runner
Run backtests on strategies before deploying live
"""

from datetime import datetime, timedelta
from backtester import Backtester
from sma_crossover_strategy import SMACrossoverStrategy
from config import settings


def run_backtest():
    """Run a backtest with the current strategy configuration"""
    
    print("\n" + "="*80)
    print("BACKTESTING CONFIGURATION")
    print("="*80)
    
    # Initialize backtester
    backtester = Backtester(
        api_key=settings.alpaca_key,
        api_secret=settings.alpaca_secret,
        initial_capital=10000
    )
    
    # Create strategy with same settings as live
    strategy = SMACrossoverStrategy(
        short_window=settings.short_window,
        long_window=settings.long_window,
        volume_threshold=settings.volume_threshold,
        stop_loss_pct=settings.stop_loss_pct
    )
    
    # Parse symbols
    symbols = settings.symbols
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(',')]
    
    # Date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Strategy: {strategy.name}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Initial Capital: $10,000")
    print(f"Short Window: {settings.short_window}")
    print(f"Long Window: {settings.long_window}")
    print(f"Volume Threshold: {settings.volume_threshold}x")
    print(f"Stop Loss: {settings.stop_loss_pct*100}%")
    print("="*80 + "\n")
    
    # Run backtest
    results = backtester.run(
        strategy=strategy,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )
    
    # Print results
    backtester.print_results()
    
    # Additional analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    if results['total_trades'] > 0:
        print(f"✓ Strategy generated trades")
        
        if results['win_rate'] >= 0.5:
            print(f"✓ Win rate above 50% ({results['win_rate']*100:.1f}%)")
        else:
            print(f"✗ Win rate below 50% ({results['win_rate']*100:.1f}%)")
        
        if results['profit_factor'] >= 1.5:
            print(f"✓ Good profit factor ({results['profit_factor']:.2f})")
        elif results['profit_factor'] >= 1.0:
            print(f"~ Marginal profit factor ({results['profit_factor']:.2f})")
        else:
            print(f"✗ Poor profit factor ({results['profit_factor']:.2f})")
        
        if results['sharpe_ratio'] >= 1.0:
            print(f"✓ Good Sharpe ratio ({results['sharpe_ratio']:.2f})")
        else:
            print(f"~ Low Sharpe ratio ({results['sharpe_ratio']:.2f})")
        
        if results['max_drawdown_pct'] > -20:
            print(f"✓ Acceptable drawdown ({results['max_drawdown_pct']:.2f}%)")
        else:
            print(f"✗ Large drawdown ({results['max_drawdown_pct']:.2f}%)")
        
        if results['total_return_pct'] > 0:
            print(f"✓ Positive returns ({results['total_return_pct']:.2f}%)")
        else:
            print(f"✗ Negative returns ({results['total_return_pct']:.2f}%)")
    else:
        print("✗ No trades generated - strategy may need adjustment")
    
    print("="*80 + "\n")
    
    # Recommendation
    if results['total_trades'] > 0 and results['total_return_pct'] > 0 and results['profit_factor'] > 1.0:
        print("✅ RECOMMENDATION: Strategy shows promise - proceed with paper trading")
    else:
        print("⚠️  RECOMMENDATION: Strategy needs improvement before live deployment")
    
    return results


if __name__ == "__main__":
    try:
        run_backtest()
    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        raise