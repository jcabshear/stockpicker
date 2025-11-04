from collections import deque
from statistics import fmean
from strategy import BaseStrategy, Signal, Position


class SMACrossoverStrategy(BaseStrategy):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, short_window: int = 5, long_window: int = 20, 
                 volume_threshold: float = 1.5, stop_loss_pct: float = 0.02):
        super().__init__("SMA_Crossover")
        self.short_window = short_window
        self.long_window = long_window
        self.volume_threshold = volume_threshold
        self.stop_loss_pct = stop_loss_pct
        
        # Store price history
        self.price_history: dict[str, deque] = {}
        self.volume_history: dict[str, deque] = {}
        self.last_signal: dict[str, str] = {}
    
    def generate_signals(self, market_data: dict) -> List[Signal]:
        signals = []
        
        for symbol, data in market_data.items():
            # Update history
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=self.long_window)
                self.volume_history[symbol] = deque(maxlen=20)
            
            self.price_history[symbol].append(data['close'])
            self.volume_history[symbol].append(data['volume'])
            
            # Need enough data
            if len(self.price_history[symbol]) < self.long_window:
                continue
            
            # Calculate SMAs
            prices = list(self.price_history[symbol])
            short_sma = fmean(prices[-self.short_window:])
            long_sma = fmean(prices)
            
            # Calculate volume ratio
            avg_volume = fmean(list(self.volume_history[symbol]))
            volume_ratio = data['volume'] / avg_volume if avg_volume > 0 else 0
            
            # Generate signal
            current_signal = None
            confidence = 0.0
            reason = ""
            
            # Bullish crossover
            if short_sma > long_sma and self.last_signal.get(symbol) != 'buy':
                if volume_ratio > self.volume_threshold:
                    current_signal = 'buy'
                    confidence = min(0.9, 0.6 + (volume_ratio - self.volume_threshold) * 0.1)
                    reason = f"Bullish SMA crossover with {volume_ratio:.1f}x volume"
            
            # Bearish crossover
            elif short_sma < long_sma and self.last_signal.get(symbol) != 'sell':
                if volume_ratio > self.volume_threshold:
                    current_signal = 'sell'
                    confidence = min(0.9, 0.6 + (volume_ratio - self.volume_threshold) * 0.1)
                    reason = f"Bearish SMA crossover with {volume_ratio:.1f}x volume"
            
            if current_signal:
                self.last_signal[symbol] = current_signal
                signals.append(Signal(
                    symbol=symbol,
                    action=current_signal,
                    confidence=confidence,
                    size=0,  # Will be calculated later
                    reason=reason,
                    timestamp=datetime.now()
                ))
        
        return signals
    
    def should_exit(self, position: Position, current_data: dict) -> bool:
        """Exit on stop loss or opposite signal"""
        # Stop loss
        if position.pnl_pct <= -self.stop_loss_pct:
            return True
        
        # Check for opposite signal
        symbol = position.symbol
        if symbol in self.price_history and len(self.price_history[symbol]) >= self.long_window:
            prices = list(self.price_history[symbol])
            short_sma = fmean(prices[-self.short_window:])
            long_sma = fmean(prices)
            
            # Exit long on bearish cross
            if position.shares > 0 and short_sma < long_sma:
                return True
            
            # Exit short on bullish cross
            if position.shares < 0 and short_sma > long_sma:
                return True
        
        return False