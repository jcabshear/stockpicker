"""
Day Trading Models
Multiple intraday trading strategies with pattern recognition
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime
import pandas as pd
from statistics import fmean


@dataclass
class TradeSignal:
    """Intraday trade signal"""
    symbol: str
    action: str  # 'buy' or 'sell'
    price: float
    confidence: float  # 0-1
    reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class BaseDayTradeModel:
    """Base class for day trading models"""
    
    def __init__(self, name: str):
        self.name = name
    
    def generate_signal(self, symbol: str, minute_bars: pd.DataFrame, 
                       screener_data: dict) -> Optional[TradeSignal]:
        """Generate buy/sell signal from minute-level data"""
        raise NotImplementedError
    
    def should_exit(self, position: dict, current_bar: dict, time: datetime) -> Tuple[bool, str]:
        """Determine if position should be closed"""
        raise NotImplementedError


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


class PatternRecognition(BaseDayTradeModel):
    """Recognizes 6 common day trading patterns"""
    
    PATTERNS = [
        'bull_flag', 'bear_flag',
        'head_shoulders', 'inverse_head_shoulders',
        'double_top', 'double_bottom',
        'triangle_breakout',
        'cup_handle',
        'engulfing'
    ]
    
    def __init__(self, patterns: List[str] = None, 
                 min_confidence: float = 0.7):
        super().__init__("Pattern_Recognition")
        self.patterns = patterns or self.PATTERNS
        self.min_confidence = min_confidence
    
    def generate_signal(self, symbol: str, minute_bars: pd.DataFrame,
                       screener_data: dict) -> Optional[TradeSignal]:
        """Scan for patterns and generate signals"""
        if len(minute_bars) < 30:
            return None
        
        # Check each pattern
        for pattern_name in self.patterns:
            method = getattr(self, f'_detect_{pattern_name}', None)
            if method:
                signal = method(symbol, minute_bars)
                if signal and signal.confidence >= self.min_confidence:
                    return signal
        
        return None
    
    def _detect_bull_flag(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect bull flag: sharp rise + consolidation + breakout"""
        if len(bars) < 30:
            return None
        
        closes = bars['close'].tolist()
        volumes = bars['volume'].tolist()
        highs = bars['high'].tolist()
        
        # Need sharp rise in first 10 bars
        initial_rise = (closes[10] - closes[0]) / closes[0]
        if initial_rise < 0.02:  # Less than 2% rise
            return None
        
        # Then consolidation for 10-15 bars (tight range)
        consolidation = closes[11:26]
        cons_range = (max(consolidation) - min(consolidation)) / fmean(consolidation)
        if cons_range > 0.015:  # More than 1.5% range
            return None
        
        # Breakout above consolidation high
        cons_high = max(consolidation)
        current_price = closes[-1]
        
        if current_price > cons_high * 1.005:  # 0.5% above high
            # Volume surge on breakout
            avg_vol = fmean(volumes[-20:-5])
            current_vol = fmean(volumes[-5:])
            volume_surge = current_vol / avg_vol if avg_vol > 0 else 0
            
            if volume_surge > 1.3:
                confidence = min(0.95, 0.7 + (volume_surge - 1.3) * 0.1)
                
                return TradeSignal(
                    symbol=symbol,
                    action='buy',
                    price=current_price,
                    confidence=confidence,
                    reason=f"Bull flag breakout +{initial_rise*100:.1f}% with {volume_surge:.1f}x volume",
                    stop_loss=cons_high * 0.995,
                    take_profit=current_price * 1.03
                )
        
        return None
    
    def _detect_bear_flag(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect bear flag: sharp drop + consolidation + breakdown"""
        if len(bars) < 30:
            return None
        
        closes = bars['close'].tolist()
        volumes = bars['volume'].tolist()
        
        # Sharp drop in first 10 bars
        initial_drop = (closes[10] - closes[0]) / closes[0]
        if initial_drop > -0.02:  # Less than 2% drop
            return None
        
        # Consolidation
        consolidation = closes[11:26]
        cons_range = (max(consolidation) - min(consolidation)) / fmean(consolidation)
        if cons_range > 0.015:
            return None
        
        # Breakdown below consolidation low
        cons_low = min(consolidation)
        current_price = closes[-1]
        
        if current_price < cons_low * 0.995:  # 0.5% below low
            avg_vol = fmean(volumes[-20:-5])
            current_vol = fmean(volumes[-5:])
            volume_surge = current_vol / avg_vol if avg_vol > 0 else 0
            
            if volume_surge > 1.3:
                confidence = min(0.95, 0.7 + (volume_surge - 1.3) * 0.1)
                
                return TradeSignal(
                    symbol=symbol,
                    action='sell',  # Short signal (skip if not shorting)
                    price=current_price,
                    confidence=confidence,
                    reason=f"Bear flag breakdown {initial_drop*100:.1f}% with {volume_surge:.1f}x volume",
                    stop_loss=cons_low * 1.005,
                    take_profit=current_price * 0.97
                )
        
        return None
    
    def _detect_head_shoulders(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect head and shoulders pattern"""
        if len(bars) < 50:
            return None
        
        highs = bars['high'].tolist()
        closes = bars['close'].tolist()
        
        # Find three peaks
        peaks = []
        for i in range(10, len(highs) - 10):
            if highs[i] > highs[i-5] and highs[i] > highs[i+5]:
                peaks.append((i, highs[i]))
        
        if len(peaks) < 3:
            return None
        
        # Get last 3 peaks
        peaks = peaks[-3:]
        left_shoulder = peaks[0][1]
        head = peaks[1][1]
        right_shoulder = peaks[2][1]
        
        # Validate H&S structure: head higher than shoulders
        if head > left_shoulder * 1.02 and head > right_shoulder * 1.02:
            if abs(left_shoulder - right_shoulder) / left_shoulder < 0.03:  # Shoulders similar
                # Find neckline (low between shoulders)
                neckline_section = closes[peaks[0][0]:peaks[2][0]]
                neckline = min(neckline_section)
                
                current_price = closes[-1]
                
                # Breakdown below neckline
                if current_price < neckline * 0.998:
                    return TradeSignal(
                        symbol=symbol,
                        action='sell',
                        price=current_price,
                        confidence=0.80,
                        reason=f"Head & shoulders breakdown below ${neckline:.2f}",
                        stop_loss=neckline * 1.01,
                        take_profit=current_price * 0.96
                    )
        
        return None
    
    def _detect_inverse_head_shoulders(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect inverse head and shoulders"""
        if len(bars) < 50:
            return None
        
        lows = bars['low'].tolist()
        closes = bars['close'].tolist()
        
        # Find three troughs
        troughs = []
        for i in range(10, len(lows) - 10):
            if lows[i] < lows[i-5] and lows[i] < lows[i+5]:
                troughs.append((i, lows[i]))
        
        if len(troughs) < 3:
            return None
        
        troughs = troughs[-3:]
        left_shoulder = troughs[0][1]
        head = troughs[1][1]
        right_shoulder = troughs[2][1]
        
        # Validate: head lower than shoulders
        if head < left_shoulder * 0.98 and head < right_shoulder * 0.98:
            if abs(left_shoulder - right_shoulder) / left_shoulder < 0.03:
                # Find neckline (high between shoulders)
                neckline_section = closes[troughs[0][0]:troughs[2][0]]
                neckline = max(neckline_section)
                
                current_price = closes[-1]
                
                # Breakout above neckline
                if current_price > neckline * 1.002:
                    return TradeSignal(
                        symbol=symbol,
                        action='buy',
                        price=current_price,
                        confidence=0.80,
                        reason=f"Inverse H&S breakout above ${neckline:.2f}",
                        stop_loss=neckline * 0.99,
                        take_profit=current_price * 1.04
                    )
        
        return None
    
    def _detect_double_top(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect double top pattern"""
        if len(bars) < 40:
            return None
        
        highs = bars['high'].tolist()
        lows = bars['low'].tolist()  # 🔧 FIX: Added missing variable definition
        closes = bars['close'].tolist()
        
        # Find two similar peaks
        peaks = []
        for i in range(10, len(highs) - 5):
            if highs[i] > highs[i-5] and highs[i] > highs[i+5]:
                peaks.append((i, highs[i]))
        
        if len(peaks) < 2:
            return None
        
        # Check last two peaks
        peak1 = peaks[-2][1]
        peak2 = peaks[-1][1]
        
        # Peaks within 1% of each other
        if abs(peak1 - peak2) / peak1 < 0.01:
            # Find valley between peaks
            valley_section = lows[peaks[-2][0]:peaks[-1][0]]
            valley = min(valley_section) if valley_section else 0
            
            current_price = closes[-1]
            
            # Breakdown below valley
            if valley > 0 and current_price < valley * 0.998:
                return TradeSignal(
                    symbol=symbol,
                    action='sell',
                    price=current_price,
                    confidence=0.75,
                    reason=f"Double top breakdown at ${peak1:.2f}",
                    stop_loss=valley * 1.01,
                    take_profit=current_price * 0.97
                )
        
        return None
    
    def _detect_double_bottom(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect double bottom pattern"""
        if len(bars) < 40:
            return None
        
        lows = bars['low'].tolist()
        closes = bars['close'].tolist()
        highs = bars['high'].tolist()
        
        # Find two similar troughs
        troughs = []
        for i in range(10, len(lows) - 5):
            if lows[i] < lows[i-5] and lows[i] < lows[i+5]:
                troughs.append((i, lows[i]))
        
        if len(troughs) < 2:
            return None
        
        trough1 = troughs[-2][1]
        trough2 = troughs[-1][1]
        
        # Troughs within 1%
        if abs(trough1 - trough2) / trough1 < 0.01:
            # Find peak between troughs
            peak_section = highs[troughs[-2][0]:troughs[-1][0]]
            peak = max(peak_section) if peak_section else 0
            
            current_price = closes[-1]
            
            # Breakout above peak
            if peak > 0 and current_price > peak * 1.002:
                return TradeSignal(
                    symbol=symbol,
                    action='buy',
                    price=current_price,
                    confidence=0.75,
                    reason=f"Double bottom breakout at ${trough1:.2f}",
                    stop_loss=peak * 0.99,
                    take_profit=current_price * 1.04
                )
        
        return None
    
    def _detect_triangle_breakout(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect triangle breakout (ascending, descending, symmetrical)"""
        if len(bars) < 30:
            return None
        
        highs = bars['high'].tolist()[-30:]
        lows = bars['low'].tolist()[-30:]
        closes = bars['close'].tolist()
        volumes = bars['volume'].tolist()
        
        # Check if range is tightening
        early_range = max(highs[:10]) - min(lows[:10])
        late_range = max(highs[-10:]) - min(lows[-10:])
        
        if late_range < early_range * 0.7:  # Range tightening by 30%
            current_price = closes[-1]
            recent_high = max(highs[-10:])
            recent_low = min(lows[-10:])
            
            # Breakout upward
            if current_price > recent_high * 1.002:
                avg_vol = fmean(volumes[-20:-5])
                current_vol = fmean(volumes[-5:])
                volume_surge = current_vol / avg_vol if avg_vol > 0 else 0
                
                if volume_surge > 1.2:
                    return TradeSignal(
                        symbol=symbol,
                        action='buy',
                        price=current_price,
                        confidence=0.78,
                        reason=f"Triangle breakout with {volume_surge:.1f}x volume",
                        stop_loss=recent_high * 0.995,
                        take_profit=current_price * 1.035
                    )
            
            # Breakdown downward
            elif current_price < recent_low * 0.998:
                avg_vol = fmean(volumes[-20:-5])
                current_vol = fmean(volumes[-5:])
                volume_surge = current_vol / avg_vol if avg_vol > 0 else 0
                
                if volume_surge > 1.2:
                    return TradeSignal(
                        symbol=symbol,
                        action='sell',
                        price=current_price,
                        confidence=0.78,
                        reason=f"Triangle breakdown with {volume_surge:.1f}x volume",
                        stop_loss=recent_low * 1.005,
                        take_profit=current_price * 0.965
                    )
        
        return None
    
    def _detect_cup_handle(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect cup and handle pattern"""
        if len(bars) < 60:
            return None
        
        closes = bars['close'].tolist()
        volumes = bars['volume'].tolist()
        
        # Cup: U-shaped price movement
        early_high = max(closes[:20])
        mid_low = min(closes[20:40])
        recent_high = max(closes[40:55])
        
        # Validate cup shape
        if mid_low < early_high * 0.90 and recent_high > early_high * 0.95:
            # Handle: slight pullback
            handle_low = min(closes[-10:])
            if handle_low > mid_low * 1.05:  # Handle should be shallow
                current_price = closes[-1]
                
                # Breakout above cup high
                if current_price > recent_high * 1.002:
                    avg_vol = fmean(volumes[-20:-5])
                    current_vol = fmean(volumes[-5:])
                    volume_surge = current_vol / avg_vol if avg_vol > 0 else 0
                    
                    if volume_surge > 1.3:
                        return TradeSignal(
                            symbol=symbol,
                            action='buy',
                            price=current_price,
                            confidence=0.82,
                            reason=f"Cup & handle breakout at ${recent_high:.2f}",
                            stop_loss=handle_low,
                            take_profit=current_price * 1.045
                        )
        
        return None
    
    def _detect_engulfing(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect bullish/bearish engulfing candle pattern"""
        if len(bars) < 10:
            return None
        
        # Get last two candles
        prev_bar = bars.iloc[-2]
        curr_bar = bars.iloc[-1]
        
        prev_open = prev_bar['open']
        prev_close = prev_bar['close']
        curr_open = curr_bar['open']
        curr_close = curr_bar['close']
        
        volumes = bars['volume'].tolist()
        
        # Bullish engulfing
        if prev_close < prev_open:  # Previous candle red
            if curr_close > curr_open:  # Current candle green
                if curr_open <= prev_close and curr_close >= prev_open:  # Engulfs
                    # Volume confirmation
                    if volumes[-1] > fmean(volumes[-10:-1]) * 1.5:
                        return TradeSignal(
                            symbol=symbol,
                            action='buy',
                            price=curr_close,
                            confidence=0.72,
                            reason="Bullish engulfing with volume",
                            stop_loss=min(prev_close, curr_open) * 0.995,
                            take_profit=curr_close * 1.03
                        )
        
        # Bearish engulfing
        elif prev_close > prev_open:  # Previous candle green
            if curr_close < curr_open:  # Current candle red
                if curr_open >= prev_close and curr_close <= prev_open:  # Engulfs
                    if volumes[-1] > fmean(volumes[-10:-1]) * 1.5:
                        return TradeSignal(
                            symbol=symbol,
                            action='sell',
                            price=curr_close,
                            confidence=0.72,
                            reason="Bearish engulfing with volume",
                            stop_loss=max(prev_close, curr_open) * 1.005,
                            take_profit=curr_close * 0.97
                        )
        
        return None
    
    def should_exit(self, position: dict, current_bar: dict, time: datetime) -> Tuple[bool, str]:
        """Exit on stop/target or time"""
        current_price = current_bar['close']
        entry_price = position['entry_price']
        
        # Stop loss
        if current_price <= entry_price * 0.98:
            return True, "Stop loss"
        
        # Take profit
        if current_price >= entry_price * 1.035:
            return True, "Take profit"
        
        # Time exit
        if time.hour == 15 and time.minute >= 40:
            return True, "End of day"
        
        return False, ""


class VWAPBounce(BaseDayTradeModel):
    """Trade bounces off VWAP with volume"""
    
    def __init__(self, vwap_threshold: float = 0.002, volume_surge: float = 1.5):
        super().__init__("VWAP_Bounce")
        self.vwap_threshold = vwap_threshold
        self.volume_surge = volume_surge
    
    def calculate_vwap(self, bars: pd.DataFrame) -> float:
        """Calculate VWAP"""
        typical_price = (bars['high'] + bars['low'] + bars['close']) / 3
        return (typical_price * bars['volume']).sum() / bars['volume'].sum()
    
    def generate_signal(self, symbol: str, minute_bars: pd.DataFrame,
                       screener_data: dict) -> Optional[TradeSignal]:
        """Generate signal on VWAP bounce"""
        if len(minute_bars) < 30:
            return None
        
        vwap = self.calculate_vwap(minute_bars)
        
        closes = minute_bars['close'].tolist()
        volumes = minute_bars['volume'].tolist()
        lows = minute_bars['low'].tolist()
        
        current_price = closes[-1]
        
        # Check if price touched VWAP recently and bounced
        touched_vwap = False
        for i in range(-5, 0):
            if abs(lows[i] - vwap) / vwap < self.vwap_threshold:
                touched_vwap = True
                break
        
        if not touched_vwap:
            return None
        
        # Now moving away from VWAP
        if current_price > vwap * 1.001:
            # Volume surge
            avg_volume = fmean(volumes[-20:-5])
            recent_volume = fmean(volumes[-5:])
            vol_ratio = recent_volume / avg_volume if avg_volume > 0 else 0
            
            if vol_ratio > self.volume_surge:
                confidence = min(0.85, 0.65 + (vol_ratio - self.volume_surge) * 0.1)
                
                return TradeSignal(
                    symbol=symbol,
                    action='buy',
                    price=current_price,
                    confidence=confidence,
                    reason=f"VWAP bounce at ${vwap:.2f} with {vol_ratio:.1f}x volume",
                    stop_loss=vwap * 0.995,
                    take_profit=current_price * 1.025
                )
        
        return None
    
    def should_exit(self, position: dict, current_bar: dict, time: datetime) -> Tuple[bool, str]:
        """Exit on stop/target or time"""
        current_price = current_bar['close']
        entry_price = position['entry_price']
        
        # Stop loss
        if current_price <= entry_price * 0.98:
            return True, "Stop loss"
        
        # Take profit
        if current_price >= entry_price * 1.025:
            return True, "Take profit"
        
        # Time exit
        if time.hour == 15 and time.minute >= 40:
            return True, "End of day"
        
        return False, ""


def get_day_trade_model(model_name: str, **kwargs) -> BaseDayTradeModel:
    """Factory function to get day trade model by name"""
    models = {
        'ma_crossover': MovingAverageCrossover,
        'pattern_recognition': PatternRecognition,
        'vwap_bounce': VWAPBounce
    }
    
    model_class = models.get(model_name.lower())
    if not model_class:
        raise ValueError(f"Unknown model: {model_name}")
    
    return model_class(**kwargs)