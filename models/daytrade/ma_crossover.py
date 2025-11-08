"""
Moving Average Crossover Model
Fast MA crosses slow MA with volume confirmation
"""

from typing import Tuple, Optional
from datetime import datetime
import pandas as pd
from statistics import fmean
from .base_model import BaseDayTradeModel, TradeSignal


class MovingAverageCrossover(BaseDayTradeModel):
    """Fast MA crosses slow MA with volume confirmation"""
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20, 
                 volume_threshold: float = 1.5):
        super().__init__("MA_Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.volume_threshold = volume_threshold
        self.last_signal = {}
    
    def generate_signal(self, symbol: str, minute_bars: pd.DataFrame,
                       screener_data: dict) -> Optional[TradeSignal]:
        """Generate signal on MA crossover"""
        if len(minute_bars) < self.slow_period:
            return None
        
        closes = minute_bars['close'].tolist()
        volumes = minute_bars['volume'].tolist()
        
        # Calculate MAs
        fast_ma = fmean(closes[-self.fast_period:])
        slow_ma = fmean(closes[-self.slow_period:])
        
        # Volume check
        avg_volume = fmean(volumes[-20:]) if len(volumes) >= 20 else fmean(volumes)
        volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 0
        
        current_price = closes[-1]
        
        # Bullish crossover
        if fast_ma > slow_ma and self.last_signal.get(symbol) != 'buy':
            if volume_ratio > self.volume_threshold:
                self.last_signal[symbol] = 'buy'
                
                # Set stop loss and take profit
                stop_loss = current_price * 0.98  # 2% stop
                take_profit = current_price * 1.04  # 4% target
                
                return TradeSignal(
                    symbol=symbol,
                    action='buy',
                    price=current_price,
                    confidence=min(0.9, 0.6 + (volume_ratio - self.volume_threshold) * 0.1),
                    reason=f"Bullish crossover with {volume_ratio:.1f}x volume",
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
        
        # Bearish crossover (for exit)
        elif fast_ma < slow_ma:
            self.last_signal[symbol] = 'sell'
        
        return None
    
    def should_exit(self, position: dict, current_bar: dict, time: datetime) -> Tuple[bool, str]:
        """Exit on stop loss, take profit, or time"""
        current_price = current_bar['close']
        entry_price = position['entry_price']
        
        # Stop loss
        if current_price <= entry_price * 0.98:
            return True, "Stop loss"
        
        # Take profit
        if current_price >= entry_price * 1.04:
            return True, "Take profit"
        
        # Time exit (3:40 PM = 15:40)
        if time.hour == 15 and time.minute >= 40:
            return True, "End of day"
        
        return False, ""
