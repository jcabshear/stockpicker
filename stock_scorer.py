"""
Multi-Factor Stock Scoring System
Evaluates stocks across technical, momentum, volume, and volatility factors
FIXED: Now uses IEX feed instead of SIP
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
try:
    import numpy as np
except ImportError:
    np = None
from statistics import fmean, stdev
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed  # ADDED: Import DataFeed


@dataclass
class ScoredStock:
    """Stock with confidence score breakdown"""
    symbol: str
    total_score: float
    technical_score: float
    momentum_score: float
    volume_score: float
    volatility_score: float
    price: float
    volume: float
    sector: str = "Unknown"
    reason: str = ""


class StockScorer:
    """Multi-factor scoring system for stock selection"""
    
    def __init__(self, api_key: str, api_secret: str, feed: str = "iex"):
        # FIXED: Store feed preference and pass to client
        self.feed = DataFeed.IEX if feed.lower() == "iex" else DataFeed.SIP
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.sector_map = self._load_sector_map()
    
    def _load_sector_map(self) -> Dict[str, str]:
        """Map common stocks to sectors for diversification"""
        return {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'META': 'Technology', 'NVDA': 'Technology', 'AMD': 'Technology',
            'TSLA': 'Automotive', 'F': 'Automotive', 'GM': 'Automotive',
            'JPM': 'Finance', 'BAC': 'Finance', 'GS': 'Finance',
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare',
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy',
            'WMT': 'Retail', 'AMZN': 'Retail', 'HD': 'Retail',
            'DIS': 'Entertainment', 'NFLX': 'Entertainment', 'CMCSA': 'Entertainment'
        }
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
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
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: List[float]) -> Tuple[float, float, float]:
        """Calculate MACD (12, 26, 9)"""
        if len(prices) < 26:
            return 0, 0, 0
        
        ema_12 = fmean(prices[-12:])
        ema_26 = fmean(prices[-26:])
        macd_line = ema_12 - ema_26
        signal_line = macd_line * 0.9
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_atr(self, bars_df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(bars_df) < period:
            return 0.0
        
        high = bars_df['high'].values
        low = bars_df['low'].values
        close = bars_df['close'].values
        
        tr_list = []
        for i in range(1, len(bars_df)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            tr_list.append(tr)
        
        return fmean(tr_list[-period:]) if tr_list else 0.0
    
    def technical_score(self, bars_df: pd.DataFrame) -> Tuple[float, str]:
        """Score: 0-40 points - Technical indicators"""
        score = 0
        reasons = []
        
        closes = bars_df['close'].tolist()
        current_price = closes[-1]
        
        # RSI (0-10 points)
        rsi = self.calculate_rsi(closes)
        if 30 < rsi < 70:
            score += 10
            reasons.append(f"RSI {rsi:.1f} in buy zone")
        elif rsi < 30:
            score += 7
            reasons.append(f"RSI {rsi:.1f} oversold")
        elif rsi > 70:
            score += 3
            reasons.append(f"RSI {rsi:.1f} overbought")
        
        # SMA positioning (0-10 points)
        if len(closes) >= 20:
            sma_20 = fmean(closes[-20:])
            if current_price > sma_20:
                score += 10
                pct_above = ((current_price - sma_20) / sma_20) * 100
                reasons.append(f"Price {pct_above:.1f}% above 20-SMA")
            else:
                score += 3
        
        # Price momentum (0-10 points)
        if len(closes) >= 2:
            price_change = (closes[-1] - closes[-2]) / closes[-2]
            if price_change > 0:
                score += 10
                reasons.append(f"Price up {price_change*100:.2f}%")
            else:
                score += 2
        
        # MACD (0-10 points)
        if len(closes) >= 26:
            macd_line, signal_line, histogram = self.calculate_macd(closes)
            if histogram > 0:
                score += 10
                reasons.append("MACD bullish")
            else:
                score += 3
        
        return score, " | ".join(reasons)
    
    def momentum_score(self, bars_df: pd.DataFrame) -> Tuple[float, str]:
        """Score: 0-25 points - Gap analysis and momentum"""
        score = 0
        reasons = []
        
        if len(bars_df) < 2:
            return 0, "Insufficient data"
        
        current = bars_df.iloc[-1]
        previous = bars_df.iloc[-2]
        
        # Gap percentage (0-15 points)
        gap = (current['open'] - previous['close']) / previous['close']
        if gap > 0.05:
            score += 15
            reasons.append(f"Large gap up {gap*100:.1f}%")
        elif gap > 0.02:
            score += 10
            reasons.append(f"Gap up {gap*100:.1f}%")
        elif gap > 0:
            score += 5
            reasons.append(f"Small gap up {gap*100:.1f}%")
        
        # Intraday momentum (0-10 points)
        intraday_change = (current['close'] - current['open']) / current['open']
        if intraday_change > 0.02:
            score += 10
            reasons.append(f"Strong intraday {intraday_change*100:.1f}%")
        elif intraday_change > 0:
            score += 5
            reasons.append(f"Positive intraday {intraday_change*100:.1f}%")
        
        return score, " | ".join(reasons)
    
    def volume_score(self, bars_df: pd.DataFrame) -> Tuple[float, str]:
        """Score: 0-20 points - Volume analysis"""
        score = 0
        reasons = []
        
        if len(bars_df) < 20:
            return 0, "Insufficient volume data"
        
        volumes = bars_df['volume'].tolist()
        current_volume = volumes[-1]
        avg_volume = fmean(volumes[-20:])
        
        # Volume ratio (0-15 points)
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        if volume_ratio > 3:
            score += 15
            reasons.append(f"Massive volume {volume_ratio:.1f}x")
        elif volume_ratio > 2:
            score += 12
            reasons.append(f"High volume {volume_ratio:.1f}x")
        elif volume_ratio > 1.5:
            score += 8
            reasons.append(f"Above avg volume {volume_ratio:.1f}x")
        elif volume_ratio > 1:
            score += 3
        
        # Volume trend (0-5 points)
        recent_avg = fmean(volumes[-5:])
        older_avg = fmean(volumes[-20:-5])
        if recent_avg > older_avg:
            score += 5
            reasons.append("Volume increasing")
        
        return score, " | ".join(reasons)
    
    def volatility_score(self, bars_df: pd.DataFrame) -> Tuple[float, str]:
        """Score: 0-15 points - Movement potential"""
        score = 0
        reasons = []
        
        if len(bars_df) < 14:
            return 0, "Insufficient data"
        
        current_price = bars_df.iloc[-1]['close']
        
        # ATR
        atr = self.calculate_atr(bars_df)
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
        
        # Goldilocks zone: 2-10% daily range (0-10 points)
        if 2 < atr_pct < 10:
            score += 10
            reasons.append(f"Good ATR {atr_pct:.1f}%")
        elif 1 < atr_pct <= 2:
            score += 5
            reasons.append(f"Low volatility {atr_pct:.1f}%")
        elif atr_pct >= 10:
            score += 3
            reasons.append(f"High volatility {atr_pct:.1f}%")
        
        # Bollinger Band position (0-5 points)
        closes = bars_df['close'].tolist()
        if len(closes) >= 20:
            sma = fmean(closes[-20:])
            std = stdev(closes[-20:])
            bb_position = (current_price - sma) / std if std > 0 else 0
            
            if -1 < bb_position < 1:
                score += 5
                reasons.append("BB middle band")
            elif bb_position < -2:
                score += 3
                reasons.append("BB lower band")
        
        return score, " | ".join(reasons)
    
    def fetch_stock_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical data for a symbol - FIXED: Uses IEX feed"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # FIXED: Specify feed parameter
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date,
                feed=self.feed  # ADDED: Use IEX feed
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            if symbol in df.index.get_level_values('symbol'):
                return df.loc[symbol]
            else:
                return pd.DataFrame()
        
        except Exception as e:
            print(f"⚠️ Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def score_stock(self, symbol: str) -> ScoredStock:
        """Calculate comprehensive score for a single stock"""
        
        bars_df = self.fetch_stock_data(symbol)
        
        if len(bars_df) < 20:
            return ScoredStock(
                symbol=symbol,
                total_score=0,
                technical_score=0,
                momentum_score=0,
                volume_score=0,
                volatility_score=0,
                price=0,
                volume=0,
                reason="Insufficient data"
            )
        
        tech_score, tech_reason = self.technical_score(bars_df)
        mom_score, mom_reason = self.momentum_score(bars_df)
        vol_score, vol_reason = self.volume_score(bars_df)
        volatility, volatility_reason = self.volatility_score(bars_df)
        
        total = (
            tech_score * 1.0 +
            mom_score * 1.0 +
            vol_score * 1.0 +
            volatility * 1.0
        )
        
        if tech_score > 30 and mom_score > 18 and vol_score > 12:
            total += 10
        
        current = bars_df.iloc[-1]
        all_reasons = [r for r in [tech_reason, mom_reason, vol_reason, volatility_reason] if r]
        
        return ScoredStock(
            symbol=symbol,
            total_score=min(total, 100),
            technical_score=tech_score,
            momentum_score=mom_score,
            volume_score=vol_score,
            volatility_score=volatility,
            price=current['close'],
            volume=current['volume'],
            sector=self.sector_map.get(symbol, "Unknown"),
            reason=" | ".join(all_reasons)
        )
    
    def screen_and_rank(self, symbols: List[str], min_score: float = 60) -> List[ScoredStock]:
        """Screen all symbols and return ranked list"""
        print(f"\n{'='*80}")
        print(f"🔍 SCREENING {len(symbols)} STOCKS (using {self.feed.name} feed)")
        print(f"{'='*80}\n")
        
        scored_stocks = []
        
        for i, symbol in enumerate(symbols, 1):
            print(f"Analyzing {symbol}... ({i}/{len(symbols)})", end='\r')
            
            try:
                scored = self.score_stock(symbol)
                
                if (scored.total_score >= min_score and 
                    scored.price > 5 and 
                    scored.volume > 100000):
                    scored_stocks.append(scored)
            
            except Exception as e:
                print(f"\n⚠️ Error scoring {symbol}: {e}")
                continue
        
        print("\n")
        scored_stocks.sort(key=lambda x: x.total_score, reverse=True)
        
        return scored_stocks
    
    def select_top_3(self, scored_stocks: List[ScoredStock]) -> List[ScoredStock]:
        """Select top 3 with sector diversification"""
        if len(scored_stocks) <= 3:
            return scored_stocks
        
        selected = []
        sectors_used = set()
        
        for stock in scored_stocks:
            if stock.sector not in sectors_used or len(selected) == 0:
                selected.append(stock)
                sectors_used.add(stock.sector)
            elif len(selected) < 3:
                selected.append(stock)
            
            if len(selected) == 3:
                break
        
        return selected
    
    def print_results(self, stocks: List[ScoredStock], title: str = "Top Stocks"):
        """Print scoring results"""
        if not stocks:
            print(f"\n{title}: No qualifying stocks found")
            return
        
        print(f"\n{'='*100}")
        print(f"{title}")
        print(f"{'='*100}")
        print(f"{'Rank':<6}{'Symbol':<8}{'Score':<8}{'Tech':<7}{'Mom':<7}{'Vol':<7}{'Volat':<7}{'Price':<10}{'Sector':<15}")
        print(f"{'-'*100}")
        
        for i, stock in enumerate(stocks, 1):
            print(f"{i:<6}{stock.symbol:<8}{stock.total_score:<8.1f}"
                  f"{stock.technical_score:<7.1f}{stock.momentum_score:<7.1f}"
                  f"{stock.volume_score:<7.1f}{stock.volatility_score:<7.1f}"
                  f"${stock.price:<9.2f}{stock.sector:<15}")
            print(f"       └─ {stock.reason}")
            print()
        
        print(f"{'='*100}\n")