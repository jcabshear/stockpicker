"""
Position Details Analysis
Provides comprehensive analysis for open positions including:
- Entry logic and reasoning
- Best/worst case scenarios
- Confidence scores
- Historical performance ratings

FIXED: Now uses IEX feed (free tier) instead of SIP data
"""

from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed  # ADDED: Import DataFeed


class PositionAnalyzer:
    """Analyze open positions with comprehensive metrics"""
    
    def __init__(self, api_key: str, api_secret: str, feed: str = "iex"):
        """
        Initialize position analyzer
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            feed: Data feed to use ('iex' for free tier, 'sip' for paid)
        """
        self.client = StockHistoricalDataClient(api_key, api_secret)
        # FIXED: Use IEX feed for free tier compatibility
        self.feed = DataFeed.IEX if feed.lower() == "iex" else DataFeed.SIP
    
    def analyze_position(self, position: dict, screening_model: str = None,
                        daytrade_model: str = None) -> dict:
        """
        Comprehensive analysis of a position
        
        Args:
            position: Dict with symbol, shares, entry_price, current_price, entry_time
            screening_model: Name of model used for selection
            daytrade_model: Name of day trading model used
            
        Returns:
            Dict with comprehensive analysis
        """
        symbol = position['symbol']
        entry_price = position['entry_price']
        current_price = position['current_price']
        shares = position['shares']
        
        # Calculate current P&L
        current_pnl = (current_price - entry_price) * shares
        current_pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Get historical data for ratings
        historical_ratings = self._calculate_historical_ratings(symbol)
        
        # Calculate scenarios
        scenarios = self._calculate_scenarios(position)
        
        # Get confidence scores
        confidences = self._calculate_confidences(symbol, current_price, entry_price)
        
        # Get entry logic
        entry_logic = self._reconstruct_entry_logic(position, screening_model, daytrade_model)
        
        # Day end options
        day_end_options = self._calculate_day_end_options(position)
        
        return {
            'symbol': symbol,
            'current_state': {
                'shares': shares,
                'entry_price': entry_price,
                'current_price': current_price,
                'entry_time': position.get('entry_time', datetime.now()).isoformat(),
                'current_pnl': current_pnl,
                'current_pnl_pct': current_pnl_pct,
                'position_value': shares * current_price
            },
            'scenarios': scenarios,
            'historical_ratings': historical_ratings,
            'confidences': confidences,
            'entry_logic': entry_logic,
            'day_end_options': day_end_options,
            'models_used': {
                'screening': screening_model or 'Unknown',
                'daytrade': daytrade_model or 'Unknown'
            }
        }
    
    def _calculate_historical_ratings(self, symbol: str) -> dict:
        """Calculate historical performance ratings with IEX feed"""
        ratings = {}
        periods = {
            '1_week': 7,
            '1_month': 30,
            '6_month': 180,
            '1_year': 365,
            '5_year': 1825
        }
        
        for period_name, days in periods.items():
            try:
                end = datetime.now()
                start = end - timedelta(days=days)
                
                # FIXED: Specify IEX feed
                request = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=TimeFrame.Day,
                    start=start,
                    end=end,
                    feed=self.feed  # Use configured feed (IEX for free tier)
                )
                
                bars = self.client.get_stock_bars(request)
                df = bars.df
                
                if df.empty or symbol not in df.index.get_level_values('symbol'):
                    raise ValueError("No data available")
                
                symbol_df = df.loc[symbol]
                
                # Calculate metrics
                start_price = symbol_df.iloc[0]['close']
                end_price = symbol_df.iloc[-1]['close']
                change_pct = ((end_price - start_price) / start_price) * 100
                
                # Determine rating
                if change_pct >= 20:
                    rating = 'Excellent'
                elif change_pct >= 10:
                    rating = 'Good'
                elif change_pct >= 0:
                    rating = 'Fair'
                elif change_pct >= -10:
                    rating = 'Poor'
                else:
                    rating = 'Very Poor'
                
                # Calculate trend strength
                prices = symbol_df['close'].values
                x = np.arange(len(prices))
                slope = np.polyfit(x, prices, 1)[0]
                trend_strength = (slope / prices[0]) * 100 if len(prices) > 0 else 0
                
                ratings[period_name] = {
                    'rating': rating,
                    'change_pct': change_pct,
                    'trend_strength': trend_strength
                }
                
            except Exception as e:
                # FIXED: Graceful error handling for free tier limitations
                print(f"Error calculating {period_name} rating for {symbol}: {e}")
                ratings[period_name] = {
                    'rating': 'N/A',
                    'change_pct': 0,
                    'trend_strength': 0,
                    'note': 'Data unavailable (using free tier IEX data)'
                }
        
        return ratings
    
    def _calculate_scenarios(self, position: dict) -> dict:
        """Calculate best/worst/expected case scenarios"""
        entry_price = position['entry_price']
        current_price = position['current_price']
        shares = position['shares']
        
        # Best case: +10% from current
        best_price = current_price * 1.10
        best_pnl = (best_price - entry_price) * shares
        
        # Worst case: -5% from current
        worst_price = current_price * 0.95
        worst_pnl = (worst_price - entry_price) * shares
        
        # Day end target: +3% from current
        day_end_price = current_price * 1.03
        day_end_pnl = (day_end_price - entry_price) * shares
        
        return {
            'best_case': {
                'target_price': best_price,
                'potential_pnl': best_pnl,
                'potential_pnl_pct': ((best_price - entry_price) / entry_price) * 100,
                'description': 'Strong momentum continuation'
            },
            'worst_case': {
                'target_price': worst_price,
                'potential_pnl': worst_pnl,
                'potential_pnl_pct': ((worst_price - entry_price) / entry_price) * 100,
                'description': 'Profit taking or reversal'
            },
            'day_end': {
                'target_price': day_end_price,
                'potential_pnl': day_end_pnl,
                'potential_pnl_pct': ((day_end_price - entry_price) / entry_price) * 100,
                'description': 'Expected closing target'
            }
        }
    
    def _calculate_confidences(self, symbol: str, current_price: float, 
                               entry_price: float) -> dict:
        """Calculate day trading and long-term confidence scores"""
        try:
            # Fetch recent data with IEX feed
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            # FIXED: Specify IEX feed
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date,
                feed=self.feed  # Use configured feed (IEX for free tier)
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            if df.empty or symbol not in df.index.get_level_values('symbol'):
                raise ValueError("No data available")
            
            symbol_df = df.loc[symbol]
            
            # Day trade confidence based on momentum and volatility
            day_score = 50  # Base score
            
            # Recent momentum (last 5 days)
            if len(symbol_df) >= 5:
                recent_change = (symbol_df['close'].iloc[-1] / symbol_df['close'].iloc[-5] - 1)
                if recent_change > 0.03:  # Up 3%+
                    day_score += 20
                elif recent_change > 0:
                    day_score += 10
            
            # Volatility (higher = better for day trading)
            if len(symbol_df) >= 20:
                volatility = symbol_df['close'].pct_change().std()
                if volatility > 0.03:  # High volatility
                    day_score += 15
                elif volatility > 0.02:
                    day_score += 10
            
            # Current position profitability
            if current_price > entry_price * 1.01:  # Already profitable
                day_score += 10
            
            # Long term confidence based on trend
            ma_20 = symbol_df['close'].tail(20).mean()
            ma_50 = symbol_df['close'].tail(50).mean() if len(symbol_df) >= 50 else ma_20
            
            long_score = 50
            if current_price > ma_20 > ma_50:  # Strong uptrend
                long_score += 35
            elif current_price > ma_20:  # Moderate uptrend
                long_score += 20
            
            # Cap scores at 100
            day_score = min(day_score, 100)
            long_score = min(long_score, 100)
            
            return {
                'day_trade': {
                    'score': day_score,
                    'level': self._score_to_level(day_score),
                    'factors': f'Momentum & volatility analysis'
                },
                'long_term': {
                    'score': long_score,
                    'level': self._score_to_level(long_score),
                    'factors': f'Trend analysis vs moving averages'
                }
            }
        except Exception as e:
            # FIXED: Return default scores on error instead of crashing
            print(f"Error calculating confidences for {symbol}: {e}")
            return {
                'day_trade': {
                    'score': 50,
                    'level': 'Medium',
                    'factors': 'Limited data available'
                },
                'long_term': {
                    'score': 50,
                    'level': 'Medium',
                    'factors': 'Limited data available'
                }
            }
    
    def _score_to_level(self, score: float) -> str:
        """Convert numerical score to confidence level"""
        if score >= 80:
            return 'Very High'
        elif score >= 65:
            return 'High'
        elif score >= 45:
            return 'Medium'
        elif score >= 30:
            return 'Low'
        else:
            return 'Very Low'
    
    def _reconstruct_entry_logic(self, position: dict, screening_model: str, 
                                 daytrade_model: str) -> dict:
        """Reconstruct the logic that led to entering this trade"""
        # FIXED: Handle None entry_time safely
        entry_time = position.get('entry_time')
        if entry_time is None:
            entry_time = datetime.now()
        
        # Convert to ISO format safely
        if hasattr(entry_time, 'isoformat'):
            timestamp_str = entry_time.isoformat()
        else:
            timestamp_str = str(entry_time)
        
        return {
            'screening_logic': self._get_screening_logic(screening_model),
            'entry_signal': self._get_entry_logic(daytrade_model),
            'timestamp': timestamp_str,
            'entry_price': position['entry_price']
        }
    
    def _get_screening_logic(self, model: str) -> str:
        """Get description of screening logic"""
        screening_descriptions = {
            'technical_momentum': 'Stock passed momentum + RSI + volume screening',
            'gap_volatility': 'Stock showed gap up with high volatility',
            'trend_strength': 'Stock in strong uptrend with MA separation',
            'manual': 'Manually selected by trader',
            None: 'Screening criteria not recorded'
        }
        return screening_descriptions.get(model, f'Selected via {model} screening')
    
    def _get_entry_logic(self, model: str) -> str:
        """Get description of entry signal logic"""
        entry_descriptions = {
            'ma_crossover': 'Fast MA crossed above slow MA with volume confirmation',
            'pattern_recognition': 'Bullish pattern detected with high confidence',
            'vwap_bounce': 'Price bounced off VWAP with volume surge',
            None: 'Entry signal not recorded'
        }
        return entry_descriptions.get(model, f'Entry via {model} signal')
    
    def _calculate_day_end_options(self, position: dict) -> List[dict]:
        """Calculate different end-of-day exit options"""
        current_price = position['current_price']
        entry_price = position['entry_price']
        shares = position['shares']
        
        options = []
        
        # Option 1: Hold overnight
        overnight_pnl = (current_price - entry_price) * shares
        options.append({
            'action': 'Hold Overnight',
            'description': 'Keep position open until tomorrow',
            'current_pnl': overnight_pnl,
            'current_pnl_pct': ((current_price - entry_price) / entry_price) * 100,
            'risk': 'Medium',
            'risk_description': 'Exposed to overnight gaps and pre-market movements'
        })
        
        # Option 2: Sell at market close
        market_close_pnl = overnight_pnl  # Same as current
        options.append({
            'action': 'Sell at Market Close',
            'description': 'Close position at 3:59 PM at market price',
            'estimated_pnl': market_close_pnl,
            'estimated_pnl_pct': ((current_price - entry_price) / entry_price) * 100,
            'risk': 'Low',
            'risk_description': 'Lock in current gains/losses, no overnight risk'
        })
        
        # Option 3: Set trailing stop
        trailing_stop_price = current_price * 0.98  # 2% trailing stop
        trailing_pnl = (trailing_stop_price - entry_price) * shares
        options.append({
            'action': 'Trailing Stop (2%)',
            'description': 'Auto-sell if price drops 2% from peak',
            'stop_price': trailing_stop_price,
            'estimated_pnl': trailing_pnl,
            'estimated_pnl_pct': ((trailing_stop_price - entry_price) / entry_price) * 100,
            'risk': 'Medium',
            'risk_description': 'Protects gains but may exit on normal volatility'
        })
        
        # Option 4: Set take profit at +5%
        take_profit_price = entry_price * 1.05
        if current_price < take_profit_price:
            take_profit_pnl = (take_profit_price - entry_price) * shares
            options.append({
                'action': 'Take Profit at +5%',
                'description': f'Auto-sell when price reaches ${take_profit_price:.2f}',
                'target_price': take_profit_price,
                'potential_pnl': take_profit_pnl,
                'potential_pnl_pct': 5.0,
                'risk': 'Low',
                'risk_description': 'Locks in 5% profit if target is reached'
            })
        
        return options


def get_live_price_data(symbol: str, api_key: str, api_secret: str) -> dict:
    """Get latest price data for charting - FIXED: Uses IEX feed"""
    try:
        client = StockHistoricalDataClient(api_key, api_secret)
        
        # Get today's minute data
        end_date = datetime.now()
        start_date = datetime.combine(end_date.date(), datetime.min.time())
        
        # FIXED: Specify IEX feed for free tier compatibility
        request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Minute,
            start=start_date,
            end=end_date,
            feed=DataFeed.IEX  # Use IEX for free tier
        )
        
        bars = client.get_stock_bars(request)
        df = bars.df
        
        if df.empty or symbol not in df.index.get_level_values('symbol'):
            return {'error': 'No data available'}
        
        symbol_df = df.loc[symbol]
        
        # Format for charting
        chart_data = []
        for timestamp, row in symbol_df.iterrows():
            chart_data.append({
                'time': timestamp.isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
        
        return {
            'symbol': symbol,
            'data': chart_data,
            'latest_price': float(symbol_df.iloc[-1]['close'])
        }
    except Exception as e:
        return {'error': str(e)}