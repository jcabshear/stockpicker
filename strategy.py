from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import pandas as pd


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0-1
    size: float  # position size in USD
    reason: str
    timestamp: datetime


@dataclass
class Position:
    """Current position"""
    symbol: str
    shares: float
    entry_price: float
    current_price: float
    entry_time: datetime
    pnl: float
    pnl_pct: float


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.positions: dict[str, Position] = {}
    
    @abstractmethod
    def generate_signals(self, market_data: dict) -> List[Signal]:
        """
        Generate trading signals based on market data
        
        Args:
            market_data: Dict with symbol -> OHLCV data
            
        Returns:
            List of Signal objects
        """
        pass
    
    @abstractmethod
    def should_exit(self, position: Position, current_data: dict) -> bool:
        """
        Determine if we should exit a position
        
        Args:
            position: Current position
            current_data: Latest market data
            
        Returns:
            True if should exit
        """
        pass
    
    def get_position_size(self, symbol: str, account_value: float, confidence: float) -> float:
        """Calculate position size based on account value and confidence"""
        # Default: risk 1-2% per trade based on confidence
        risk_pct = 0.01 + (confidence * 0.01)
        return account_value * risk_pct