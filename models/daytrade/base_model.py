"""
Base Day Trading Model Classes
Shared functionality for all intraday trading models
"""

from dataclasses import dataclass
from typing import Tuple, Optional
from datetime import datetime
import pandas as pd


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
