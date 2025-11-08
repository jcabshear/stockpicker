"""
Gap Volatility Screener
Screens for gap ups/downs with volatility and breakout potential
"""

from typing import List
from statistics import fmean
import pandas as pd
from .base_screener import BaseScreener, ScreenedStock


class GapVolatilityScreener(BaseScreener):
    """Screen for gap ups/downs with volatility and breakout potential"""
    
    def __init__(self, api_key: str, api_secret: str,
                 min_gap: float = 0.02,
                 min_atr_pct: float = 2.0,
                 max_atr_pct: float = 8.0):
        super().__init__(api_key, api_secret)
        self.min_gap = min_gap
        self.min_atr_pct = min_atr_pct
        self.max_atr_pct = max_atr_pct
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(df) < period:
            return 0.0
        
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        tr_list = []
        for i in range(1, len(df)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            tr_list.append(tr)
        
        return fmean(tr_list[-period:]) if tr_list else 0.0
    
    def screen(self, symbols: List[str], min_score: float = 60) -> List[ScreenedStock]:
        """Screen for gap and volatility plays"""
        results = []
        
        for symbol in symbols:
            try:
                df = self.fetch_data(symbol)
                if len(df) < 20:
                    continue
                
                current = df.iloc[-1]
                previous = df.iloc[-2]
                
                current_price = current['close']
                
                # Calculate gap
                gap = (current['open'] - previous['close']) / previous['close']
                
                # Calculate ATR
                atr = self.calculate_atr(df)
                atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
                
                # Volume surge
                volumes = df['volume'].tolist()
                avg_volume = fmean(volumes[-20:])
                volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 0
                
                # Intraday follow-through
                intraday_move = (current['close'] - current['open']) / current['open']
                follow_through = (gap > 0 and intraday_move > 0) or (gap < 0 and intraday_move < 0)
                
                # Score (0-100)
                score = 0
                reasons = []
                
                # Gap score (0-35)
                if abs(gap) > 0.05:
                    score += 35
                    reasons.append(f"Large gap {gap*100:.1f}%")
                elif abs(gap) > self.min_gap:
                    score += 20
                    reasons.append(f"Gap {gap*100:.1f}%")
                
                # Volatility score (0-25)
                if self.min_atr_pct < atr_pct < self.max_atr_pct:
                    score += 25
                    reasons.append(f"Ideal ATR {atr_pct:.1f}%")
                elif atr_pct >= self.max_atr_pct:
                    score += 10
                    reasons.append(f"High volatility {atr_pct:.1f}%")
                
                # Volume score (0-20)
                if volume_ratio > 2:
                    score += 20
                    reasons.append(f"Volume surge {volume_ratio:.1f}x")
                elif volume_ratio > 1.5:
                    score += 10
                
                # Follow-through score (0-20)
                if follow_through:
                    score += 20
                    reasons.append(f"Gap follow-through {intraday_move*100:.1f}%")
                
                if score >= min_score and abs(gap) >= self.min_gap:
                    results.append(ScreenedStock(
                        symbol=symbol,
                        score=score,
                        price=current_price,
                        volume=volumes[-1],
                        reason=" | ".join(reasons),
                        metadata={
                            'gap': gap,
                            'atr_pct': atr_pct,
                            'volume_ratio': volume_ratio,
                            'follow_through': follow_through
                        }
                    ))
            except Exception as e:
                continue
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
