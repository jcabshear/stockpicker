"""
Pattern Recognition Model
Recognizes common day trading patterns
Includes: Bull/Bear flags, Head & Shoulders, Double Tops/Bottoms, Triangles, Cup & Handle, Engulfing
"""

from typing import List, Tuple, Optional
from datetime import datetime
import pandas as pd
from statistics import fmean
from .base_model import BaseDayTradeModel, TradeSignal


class PatternRecognition(BaseDayTradeModel):
    """Recognizes 9 common day trading patterns"""
    
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
        """Detect bullish flag pattern"""
        if len(bars) < 40:
            return None
        
        closes = bars['close'].tolist()
        volumes = bars['volume'].tolist()
        highs = bars['high'].tolist()
        
        # Look for initial strong move up (pole)
        initial_move = (closes[-20] - closes[-30]) / closes[-30] if len(closes) >= 30 else 0
        
        if initial_move < 0.03:  # Need 3%+ move
            return None
        
        # Look for consolidation (flag)
        consolidation = closes[-15:]
        cons_range = (max(consolidation) - min(consolidation)) / fmean(consolidation)
        if cons_range > 0.015:  # Too wide
            return None
        
        # Breakout above consolidation high
        cons_high = max(consolidation)
        current_price = closes[-1]
        
        if current_price > cons_high * 1.005:  # 0.5% above high
            avg_vol = fmean(volumes[-20:-5])
            current_vol = fmean(volumes[-5:])
            volume_surge = current_vol / avg_vol if avg_vol > 0 else 0
            
            if volume_surge > 1.3:
                confidence = min(0.90, 0.7 + (volume_surge - 1.3) * 0.1)
                
                return TradeSignal(
                    symbol=symbol,
                    action='buy',
                    price=current_price,
                    confidence=confidence,
                    reason=f"Bull flag breakout {initial_move*100:.1f}% with {volume_surge:.1f}x volume",
                    stop_loss=cons_high * 0.995,
                    take_profit=current_price * 1.04
                )
        
        return None
    
    def _detect_bear_flag(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect bearish flag pattern"""
        if len(bars) < 40:
            return None
        
        closes = bars['close'].tolist()
        volumes = bars['volume'].tolist()
        lows = bars['low'].tolist()
        
        # Initial strong drop
        initial_drop = (closes[-30] - closes[-20]) / closes[-30] if len(closes) >= 30 else 0
        
        if initial_drop < 0.03:
            return None
        
        # Consolidation
        consolidation = closes[-15:]
        cons_range = (max(consolidation) - min(consolidation)) / fmean(consolidation)
        if cons_range > 0.015:
            return None
        
        # Breakdown below consolidation low
        cons_low = min(consolidation)
        current_price = closes[-1]
        
        if current_price < cons_low * 0.995:
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
        """Detect head and shoulders pattern (bearish)"""
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
        
        # Validate H&S structure
        if head > left_shoulder * 1.02 and head > right_shoulder * 1.02:
            if abs(left_shoulder - right_shoulder) / left_shoulder < 0.03:
                # Find neckline
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
                        reason=f"Head & shoulders breakdown at neckline ${neckline:.2f}",
                        stop_loss=neckline * 1.01,
                        take_profit=current_price * 0.96
                    )
        
        return None
    
    def _detect_inverse_head_shoulders(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect inverse head and shoulders pattern (bullish)"""
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
        
        # Get last 3 troughs
        troughs = troughs[-3:]
        left_shoulder = troughs[0][1]
        head = troughs[1][1]
        right_shoulder = troughs[2][1]
        
        # Validate inverse H&S
        if head < left_shoulder * 0.98 and head < right_shoulder * 0.98:
            if abs(left_shoulder - right_shoulder) / left_shoulder < 0.03:
                # Find neckline
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
                        reason=f"Inverse H&S breakout at neckline ${neckline:.2f}",
                        stop_loss=neckline * 0.99,
                        take_profit=current_price * 1.04
                    )
        
        return None
    
    def _detect_double_top(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect double top pattern (bearish)"""
        if len(bars) < 40:
            return None
        
        highs = bars['high'].tolist()
        lows = bars['low'].tolist()
        closes = bars['close'].tolist()
        
        # Find recent peaks
        peaks = []
        for i in range(10, len(highs) - 5):
            if highs[i] > highs[i-5] and highs[i] > highs[i+5]:
                peaks.append((i, highs[i]))
        
        if len(peaks) < 2:
            return None
        
        # Check last two peaks
        peak1 = peaks[-2][1]
        peak2 = peaks[-1][1]
        
        # Peaks within 1%
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
        """Detect double bottom pattern (bullish)"""
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
        """Detect triangle breakout (ascending/descending/symmetrical)"""
        if len(bars) < 30:
            return None
        
        closes = bars['close'].tolist()
        highs = bars['high'].tolist()
        lows = bars['low'].tolist()
        volumes = bars['volume'].tolist()
        
        # Get recent range
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        
        range_start = max(recent_highs[:10]) - min(recent_lows[:10])
        range_end = max(recent_highs[-10:]) - min(recent_lows[-10:])
        
        # Range should be compressing
        if range_end >= range_start * 0.8:
            return None
        
        # Check for breakout
        current_price = closes[-1]
        upper_bound = max(recent_highs)
        lower_bound = min(recent_lows)
        
        # Volume surge on breakout
        avg_vol = fmean(volumes[-20:-5])
        current_vol = volumes[-1]
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 0
        
        # Upward breakout
        if current_price > upper_bound * 1.005 and vol_ratio > 1.5:
            return TradeSignal(
                symbol=symbol,
                action='buy',
                price=current_price,
                confidence=0.78,
                reason=f"Triangle breakout with {vol_ratio:.1f}x volume",
                stop_loss=upper_bound * 0.99,
                take_profit=current_price * 1.03
            )
        
        # Downward breakdown
        elif current_price < lower_bound * 0.995 and vol_ratio > 1.5:
            return TradeSignal(
                symbol=symbol,
                action='sell',
                price=current_price,
                confidence=0.78,
                reason=f"Triangle breakdown with {vol_ratio:.1f}x volume",
                stop_loss=lower_bound * 1.01,
                take_profit=current_price * 0.97
            )
        
        return None
    
    def _detect_cup_handle(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect cup and handle pattern (bullish)"""
        if len(bars) < 50:
            return None
        
        closes = bars['close'].tolist()
        highs = bars['high'].tolist()
        
        # Find cup formation (U-shape)
        cup_start_price = closes[-50]
        cup_low = min(closes[-50:-10])
        cup_recovery = closes[-10]
        
        # Cup should be rounded
        cup_depth = (cup_start_price - cup_low) / cup_start_price
        if not (0.10 < cup_depth < 0.35):
            return None
        
        # Price should recover near cup start
        if abs(cup_recovery - cup_start_price) / cup_start_price > 0.05:
            return None
        
        # Handle (slight pullback)
        handle = closes[-10:]
        handle_low = min(handle)
        handle_pullback = (cup_recovery - handle_low) / cup_recovery
        
        if not (0.03 < handle_pullback < 0.15):
            return None
        
        # Breakout above cup/handle high
        current_price = closes[-1]
        breakout_level = max(highs[-50:])
        
        if current_price > breakout_level * 1.005:
            return TradeSignal(
                symbol=symbol,
                action='buy',
                price=current_price,
                confidence=0.82,
                reason=f"Cup & handle breakout, depth {cup_depth*100:.1f}%",
                stop_loss=handle_low * 0.995,
                take_profit=current_price * 1.05
            )
        
        return None
    
    def _detect_engulfing(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Detect bullish/bearish engulfing candles"""
        if len(bars) < 10:
            return None
        
        prev = bars.iloc[-2]
        curr = bars.iloc[-1]
        
        prev_open = prev['open']
        prev_close = prev['close']
        curr_open = curr['open']
        curr_close = curr['close']
        
        volumes = bars['volume'].tolist()
        
        # Bullish engulfing
        if prev_close < prev_open:  # Previous candle red
            if curr_close > curr_open:  # Current candle green
                if curr_open <= prev_close and curr_close >= prev_open:  # Engulfs
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
