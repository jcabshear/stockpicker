"""
Trend Strength Screener
Screens for sustained multi-day trends with MA alignment
"""

from typing import List
from statistics import fmean
from .base_screener import BaseScreener, ScreenedStock


class TrendStrengthScreener(BaseScreener):
    """Screen for sustained multi-day trends with MA alignment"""
    
    def __init__(self, api_key: str, api_secret: str,
                 min_trend_days: int = 3,
                 min_ma_separation: float = 0.02):
        super().__init__(api_key, api_secret)
        self.min_trend_days = min_trend_days
        self.min_ma_separation = min_ma_separation
    
    def screen(self, symbols: List[str], min_score: float = 60) -> List[ScreenedStock]:
        """Screen for trend strength"""
        results = []
        
        for symbol in symbols:
            try:
                df = self.fetch_data(symbol)
                if len(df) < 50:
                    continue
                
                closes = df['close'].tolist()
                volumes = df['volume'].tolist()
                
                current_price = closes[-1]
                
                # Calculate moving averages
                sma_20 = fmean(closes[-20:])
                sma_50 = fmean(closes[-50:])
                
                # MA alignment (bullish when 20 > 50)
                bullish_alignment = sma_20 > sma_50
                ma_sep_20_50 = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
                
                # Count consecutive up days
                up_days = 0
                for i in range(len(closes) - 1, max(0, len(closes) - 10), -1):
                    if closes[i] > closes[i-1]:
                        up_days += 1
                    else:
                        break
                
                # Price above all MAs
                above_all_mas = current_price > sma_20 > sma_50
                
                # Volume trending up
                vol_recent = fmean(volumes[-5:])
                vol_older = fmean(volumes[-20:-5])
                volume_trending = vol_recent > vol_older if vol_older > 0 else False
                
                # Score (0-100)
                score = 0
                reasons = []
                
                # MA alignment (0-20)
                if bullish_alignment:
                    score += 20
                    reasons.append("Bullish MA alignment")
                
                # Consecutive up days (0-15)
                if up_days >= 5:
                    score += 15
                    reasons.append(f"{up_days} consecutive up days")
                elif up_days >= self.min_trend_days:
                    score += 10
                    reasons.append(f"{up_days} up days")
                
                # MA separation (0-20)
                if ma_sep_20_50 > self.min_ma_separation:
                    score += 20
                    reasons.append(f"Strong MA separation {ma_sep_20_50*100:.1f}%")
                elif ma_sep_20_50 > 0:
                    score += 10
                
                # Price position (0-15)
                if above_all_mas:
                    score += 15
                    reasons.append("Price above all MAs")
                
                # Volume trend (0-10)
                if volume_trending:
                    score += 10
                    reasons.append("Volume trending up")
                
                # Bonus for perfect setup (0-20)
                if bullish_alignment and above_all_mas and up_days >= 5:
                    score += 20
                    reasons.append("Perfect trend setup")
                
                if score >= min_score:
                    results.append(ScreenedStock(
                        symbol=symbol,
                        score=score,
                        price=current_price,
                        volume=volumes[-1],
                        reason=" | ".join(reasons),
                        metadata={
                            'bullish_alignment': bullish_alignment,
                            'consecutive_up_days': up_days,
                            'ma_separation': ma_sep_20_50,
                            'above_all_mas': above_all_mas
                        }
                    ))
            except Exception as e:
                continue
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
