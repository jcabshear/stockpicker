"""
Base Screener Classes and Common Utilities
Shared functionality for all screening models
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from statistics import fmean


@dataclass
class ScreenedStock:
    """Result from screening"""
    symbol: str
    score: float
    price: float
    volume: int
    reason: str
    metadata: dict


class BaseScreener:
    """Base class for all screening models"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.client = StockHistoricalDataClient(api_key, api_secret)
    
    def fetch_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical data for screening"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            if symbol in df.index.get_level_values('symbol'):
                return df.loc[symbol]
            else:
                return pd.DataFrame()
        
        except Exception as e:
            return pd.DataFrame()
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = fmean(gains[-period:]) if gains[-period:] else 0
        avg_loss = fmean(losses[-period:]) if losses[-period:] else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def screen(self, symbols: List[str], min_score: float = 60) -> List[ScreenedStock]:
        """Override in subclass"""
        raise NotImplementedError
