"""
Advanced Screening Models
Three different approaches to daily stock screening
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import pandas as pd
from statistics import fmean, stdev
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed


@dataclass
class ScreenedStock:
    """Stock that passed screening criteria"""
    symbol: str
    score: float
    price: float
    volume: float
    reason: str
    metadata: Dict  # Model-specific data


class BaseScreener:
    """Base class for screening models"""
    
    def __init__(self, api_key: str, api_secret: str, feed: str = "iex"):
        self.feed = DataFeed.IEX if feed.lower() == "iex" else DataFeed.SIP
        self.client = StockHistoricalDataClient(api_key, api_secret)
    
    def fetch_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date,
                feed=self.feed
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            if symbol in df.index.get_level_values('symbol'):
                return df.loc[symbol]
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = fmean(gains[-period:])
        avg_loss = fmean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def screen(self, symbols: List[str], min_score: float = 60) -> List[ScreenedStock]:
        """Override in subclass"""
        raise NotImplementedError


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
        """Calculate ATR"""
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
                
                # Calculate MAs
                sma_10 = fmean(closes[-10:])
                sma_20 = fmean(closes[-20:])
                sma_50 = fmean(closes[-50:])
                
                # MA alignment (bullish: 10 > 20 > 50)
                bullish_alignment = sma_10 > sma_20 > sma_50
                bearish_alignment = sma_10 < sma_20 < sma_50
                
                # Trend consistency (consecutive up days)
                up_days = 0
                for i in range(len(closes)-1, max(0, len(closes)-10), -1):
                    if i > 0 and closes[i] > closes[i-1]:
                        up_days += 1
                    else:
                        break
                
                # MA separation
                ma_sep_20_50 = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0
                
                # Volume trend
                recent_vol = fmean(volumes[-5:])
                older_vol = fmean(volumes[-20:-5])
                volume_trending = recent_vol > older_vol
                
                # Price vs MAs
                above_all_mas = current_price > sma_10 > sma_20 > sma_50
                
                # Score (0-100)
                score = 0
                reasons = []
                
                # Alignment score (0-30)
                if bullish_alignment:
                    score += 30
                    reasons.append("Bullish MA alignment")
                elif bearish_alignment:
                    score += 15
                    reasons.append("Bearish MA alignment")
                
                # Trend consistency (0-25)
                if up_days >= 5:
                    score += 25
                    reasons.append(f"{up_days} consecutive up days")
                elif up_days >= self.min_trend_days:
                    score += 15
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


def get_screener(model_name: str, api_key: str, api_secret: str, **kwargs) -> BaseScreener:
    """Factory function to get screener by name"""
    screeners = {
        'technical_momentum': TechnicalMomentumScreener,
        'gap_volatility': GapVolatilityScreener,
        'trend_strength': TrendStrengthScreener
    }
    
    screener_class = screeners.get(model_name.lower())
    if not screener_class:
        raise ValueError(f"Unknown screener: {model_name}")
    
    return screener_class(api_key, api_secret, **kwargs)