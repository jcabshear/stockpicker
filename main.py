import asyncio
from datetime import datetime, timedelta
from sma_crossover_strategy import SMACrossoverStrategy
from backtester import Backtester
from live_trader import LiveTrader
from config import settings


async def main():
    # Define your strategy
    strategy = SMACrossoverStrategy(
        short_window=5,
        long_window=20,
        volume_threshold=1.5,
        stop_loss_pct=0.02
    )
    
    # Symbols to trade
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMD", "META"]
    
    # Choose mode
    mode = "backtest"  # or "live"
    
    if mode == "backtest":
        # Backtest
        backtester = Backtester(
            settings.alpaca_key,
            settings.alpaca_secret,
            initial_capital=100000
        )
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        results = backtester.run(strategy, symbols, start_date, end_date)
        backtester.print_results()
        
        # Save results
        results['trades'].to_csv('backtest_trades.csv')
        results['equity_curve'].to_csv('backtest_equity.csv')
    
    elif mode == "live":
        # Live trading
        trader = LiveTrader(strategy)
        await trader.run(symbols)


if __name__ == "__main__":
    asyncio.run(main())