"""
Technical Momentum Screener
Screens based on RSI, volume surge, momentum, and SMA positioning
"""

from typing import List
from statistics import fmean
from .base_screener import BaseScreener, ScreenedStock


class TechnicalMomentumScreener(BaseScreener):
    """Screen based on RSI, MACD, volume surge, and momentum"""
    
    def __init__(self, api_key: str, api_secret: str, 
                 rsi_min: float = 40, rsi_max: float = 70,
                 volume_min: float = 1.5,
                 momentum_threshold: float = 0.02):
        super().__init__(api_key, api_secret)
        self.rsi_min = rsi_min
        self.rsi_max = rsi_max
        self.volume_min = volume_min
        self.momentum_threshold = momentum_threshold
    
    def screen(self, symbols: List[str], min_score: float = 60) -> List[ScreenedStock]:
        """Screen for technical momentum"""
        results = []
        
        for symbol in symbols:
            try:
                df = self.fetch_data(symbol)
                if len(df) < 20:
                    continue
                
                closes = df['close'].tolist()
                volumes = df['volume'].tolist()
                
                # Calculate metrics
                current_price = closes[-1]
                rsi = self.calculate_rsi(closes)
                
                # Volume ratio
                avg_volume = fmean(volumes[-20:])
                volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 0
                
                # Price momentum (last 3 days)
                momentum = (closes[-1] - closes[-4]) / closes[-4] if len(closes) >= 4 else 0
                
                # SMA positioning
                sma_20 = fmean(closes[-20:])
                above_sma = current_price > sma_20
                
                # Score (0-100)
                score = 0
                reasons = []
                
                # RSI score (0-25)
                if self.rsi_min < rsi < self.rsi_max:
                    score += 25
                    reasons.append(f"RSI {rsi:.1f} optimal")
                elif rsi < self.rsi_min:
                    score += 15
                    reasons.append(f"RSI {rsi:.1f} oversold")
                
                # Volume score (0-25)
                if volume_ratio > self.volume_min * 1.5:
                    score += 25
                    reasons.append(f"Volume surge {volume_ratio:.1f}x")
                elif volume_ratio > self.volume_min:
                    score += 15
                    reasons.append(f"Volume {volume_ratio:.1f}x")
                
                # Momentum score (0-25)
                if momentum > self.momentum_threshold:
                    score += 25
                    reasons.append(f"Strong momentum +{momentum*100:.1f}%")
                elif momentum > 0:
                    score += 10
                    reasons.append(f"Positive momentum")
                
                # Position score (0-25)
                if above_sma:
                    score += 25
                    pct = ((current_price - sma_20) / sma_20) * 100
                    reasons.append(f"{pct:.1f}% above SMA")
                
                if score >= min_score:
                    results.append(ScreenedStock(
                        symbol=symbol,
                        score=score,
                        price=current_price,
                        volume=volumes[-1],
                        reason=" | ".join(reasons),
                        metadata={
                            'rsi': rsi,
                            'volume_ratio': volume_ratio,
                            'momentum': momentum,
                            'above_sma': above_sma
                        }
                    ))
            except Exception as e:
                continue
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
