"""
VWAP Bounce Model
Trade bounces off VWAP with volume confirmation
"""

from typing import Tuple, Optional
from datetime import datetime
import pandas as pd
from statistics import fmean
from .base_model import BaseDayTradeModel, TradeSignal


class VWAPBounce(BaseDayTradeModel):
    """Trade bounces off VWAP with volume"""
    
    def __init__(self, vwap_threshold: float = 0.002, volume_surge: float = 1.5):
        super().__init__("VWAP_Bounce")
        self.vwap_threshold = vwap_threshold
        self.volume_surge = volume_surge
    
    def calculate_vwap(self, bars: pd.DataFrame) -> float:
        """Calculate Volume Weighted Average Price"""
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
