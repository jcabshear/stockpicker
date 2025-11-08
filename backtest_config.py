"""
Backtest Configuration
======================
Centralized configuration for backtesting with daily allocation control
"""

from dataclasses import dataclass
from typing import List


@dataclass
class BacktestConfig:
    """Configuration for enhanced backtesting"""
    
    # Capital Settings
    initial_capital: float = 10000  # Starting capital
    daily_allocation_pct: float = 0.10  # 10% of buying power per day
    
    # Trading Rules
    top_n_stocks: int = 2  # Number of stocks to trade per day
    settlement_days: int = 2  # T+2 settlement period
    
    # Data Feed
    feed: str = "iex"  # Use "iex" for free tier, "sip" for paid
    
    # Strategy Parameters
    short_window: int = 5
    long_window: int = 20
    volume_threshold: float = 1.5
    stop_loss_pct: float = 0.02
    
    # Symbols to Trade
    symbols: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    def get_per_stock_allocation(self) -> float:
        """Calculate how much to allocate per stock"""
        return (self.initial_capital * self.daily_allocation_pct) / self.top_n_stocks
    
    def print_config(self):
        """Print configuration summary"""
        print(f"\n{'='*80}")
        print("BACKTEST CONFIGURATION")
        print(f"{'='*80}")
        print(f"\n📊 Capital Management:")
        print(f"   Initial Capital: ${self.initial_capital:,.2f}")
        print(f"   Daily Allocation: {self.daily_allocation_pct*100:.1f}% = ${self.initial_capital * self.daily_allocation_pct:,.2f}")
        print(f"   Stocks Per Day: {self.top_n_stocks}")
        print(f"   Per Stock Allocation: ${self.get_per_stock_allocation():,.2f}")
        print(f"   Settlement Period: T+{self.settlement_days}")
        print(f"\n📈 Strategy Parameters:")
        print(f"   Short SMA: {self.short_window} periods")
        print(f"   Long SMA: {self.long_window} periods")
        print(f"   Volume Threshold: {self.volume_threshold}x average")
        print(f"   Stop Loss: {self.stop_loss_pct*100:.1f}%")
        print(f"\n🎯 Trading Universe:")
        print(f"   Symbols: {', '.join(self.symbols)}")
        print(f"   Data Feed: {self.feed.upper()}")
        print(f"{'='*80}\n")


# Preset Configurations
# =====================

def get_conservative_config() -> BacktestConfig:
    """Conservative configuration - lower risk"""
    return BacktestConfig(
        initial_capital=10000,
        daily_allocation_pct=0.05,  # Only 5% per day
        top_n_stocks=1,  # Only 1 stock at a time
        settlement_days=2,
        short_window=10,
        long_window=30,
        volume_threshold=2.0,  # Higher volume requirement
        stop_loss_pct=0.015,  # Tighter stop loss (1.5%)
        symbols=['AAPL', 'MSFT', 'JNJ', 'PG']  # More stable stocks
    )


def get_aggressive_config() -> BacktestConfig:
    """Aggressive configuration - higher risk/reward"""
    return BacktestConfig(
        initial_capital=10000,
        daily_allocation_pct=0.20,  # 20% per day
        top_n_stocks=3,  # Trade 3 stocks
        settlement_days=2,
        short_window=3,
        long_window=10,
        volume_threshold=1.2,  # Lower volume requirement
        stop_loss_pct=0.03,  # Wider stop loss (3%)
        symbols=['TSLA', 'NVDA', 'AMD', 'PLTR', 'COIN']  # More volatile stocks
    )


def get_balanced_config() -> BacktestConfig:
    """Balanced configuration - moderate risk"""
    return BacktestConfig(
        initial_capital=10000,
        daily_allocation_pct=0.10,  # 10% per day
        top_n_stocks=2,  # Trade 2 stocks
        settlement_days=2,
        short_window=5,
        long_window=20,
        volume_threshold=1.5,
        stop_loss_pct=0.02,  # 2% stop loss
        symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    )


# Example: Custom Configuration
# ==============================

def get_custom_config() -> BacktestConfig:
    """
    Create your own custom configuration here
    
    Example: Day Trading Setup
    - Higher daily allocation (we're in and out same day)
    - More stocks (diversification)
    - Tighter parameters (faster signals)
    """
    return BacktestConfig(
        initial_capital=10000,
        daily_allocation_pct=0.15,  # 15% per day
        top_n_stocks=3,  # Trade up to 3 stocks per day
        settlement_days=2,
        short_window=3,  # Fast SMA
        long_window=8,  # Medium SMA
        volume_threshold=1.3,
        stop_loss_pct=0.025,  # 2.5% stop
        symbols=['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD'],
        feed="iex"
    )


if __name__ == "__main__":
    # Show all configurations
    print("\n" + "="*80)
    print("AVAILABLE CONFIGURATIONS")
    print("="*80)
    
    configs = {
        'Conservative': get_conservative_config(),
        'Balanced': get_balanced_config(),
        'Aggressive': get_aggressive_config(),
        'Custom': get_custom_config()
    }
    
    for name, config in configs.items():
        print(f"\n{name.upper()}")
        print(f"{'-'*80}")
        print(f"Daily Allocation: {config.daily_allocation_pct*100:.1f}%")
        print(f"Per Stock: ${config.get_per_stock_allocation():,.2f}")
        print(f"Max Stocks/Day: {config.top_n_stocks}")
        print(f"Risk Level: ", end="")
        
        if config.daily_allocation_pct <= 0.05:
            print("🟢 LOW")
        elif config.daily_allocation_pct <= 0.10:
            print("🟡 MEDIUM")
        else:
            print("🔴 HIGH")