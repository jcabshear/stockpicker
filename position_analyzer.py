"""
Position Details Analysis
Provides comprehensive analysis for open positions including:
- Entry logic and reasoning
- Best/worst case scenarios
- Confidence scores
- Historical performance ratings
"""

from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


class PositionAnalyzer:
    """Analyze open positions with comprehensive metrics"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.client = StockHistoricalDataClient(api_key, api_secret)
    
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
                'position_value': current_price * shares
            },
            'entry_logic': entry_logic,
            'scenarios': scenarios,
            'confidences': confidences,
            'historical_ratings': historical_ratings,
            'day_end_options': day_end_options,
            'models_used': {
                'screening': screening_model or 'Unknown',
                'daytrade': daytrade_model or 'Unknown'
            }
        }
    
    def _calculate_historical_ratings(self, symbol: str) -> dict:
        """
        Calculate bull/bear ratings for different time periods
        
        Returns ratings: Strong Bull, Bull, Soft Bull, Neutral, Soft Bear, Bear, Strong Bear
        """
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
                # Fetch historical data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                request = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=TimeFrame.Day,
                    start=start_date,
                    end=end_date
                )
                
                bars = self.client.get_stock_bars(request)
                df = bars.df
                
                if df.empty or symbol not in df.index.get_level_values('symbol'):
                    ratings[period_name] = {'rating': 'Unknown', 'score': 0, 'change_pct': 0}
                    continue
                
                symbol_df = df.loc[symbol]
                
                # Calculate return
                first_price = symbol_df.iloc[0]['close']
                last_price = symbol_df.iloc[-1]['close']
                return_pct = ((last_price - first_price) / first_price) * 100
                
                # Calculate volatility (standard deviation of returns)
                returns = symbol_df['close'].pct_change()
                volatility = returns.std() * np.sqrt(252) * 100  # Annualized
                
                # Calculate trend strength (% of days price increased)
                up_days = (symbol_df['close'].diff() > 0).sum()
                trend_strength = (up_days / len(symbol_df)) * 100
                
                # Determine rating based on return and trend
                rating, score = self._classify_rating(return_pct, trend_strength, volatility)
                
                ratings[period_name] = {
                    'rating': rating,
                    'score': score,
                    'change_pct': return_pct,
                    'volatility': volatility,
                    'trend_strength': trend_strength
                }
            except Exception as e:
                print(f"Error calculating {period_name} rating for {symbol}: {e}")
                ratings[period_name] = {'rating': 'Unknown', 'score': 0, 'change_pct': 0}
        
        return ratings
    
    def _classify_rating(self, return_pct: float, trend_strength: float, volatility: float) -> tuple:
        """
        Classify into bull/bear categories
        
        Returns: (rating_name, numerical_score)
        """
        # Strong Bull: >20% return, >60% up days, <30% volatility
        if return_pct > 20 and trend_strength > 60 and volatility < 30:
            return ('Strong Bull', 95)
        
        # Bull: >10% return, >55% up days
        elif return_pct > 10 and trend_strength > 55:
            return ('Bull', 75)
        
        # Soft Bull: >5% return, >50% up days
        elif return_pct > 5 and trend_strength > 50:
            return ('Soft Bull', 60)
        
        # Soft Bear: -5% to 0% return
        elif -5 < return_pct <= 0:
            return ('Soft Bear', 40)
        
        # Bear: -15% to -5% return
        elif -15 < return_pct <= -5:
            return ('Bear', 25)
        
        # Strong Bear: <-15% return
        elif return_pct <= -15:
            return ('Strong Bear', 5)
        
        # Neutral: 0-5% return
        else:
            return ('Neutral', 50)
    
    def _calculate_scenarios(self, position: dict) -> dict:
        """Calculate best case, worst case, and day end scenarios"""
        entry_price = position['entry_price']
        current_price = position['current_price']
        shares = position['shares']
        
        # Best case: +10% from current
        best_case_price = current_price * 1.10
        best_case_pnl = (best_case_price - entry_price) * shares
        best_case_pct = ((best_case_price - entry_price) / entry_price) * 100
        
        # Worst case: -5% from current
        worst_case_price = current_price * 0.95
        worst_case_pnl = (worst_case_price - entry_price) * shares
        worst_case_pct = ((worst_case_price - entry_price) / entry_price) * 100
        
        # Day end: +3% from current (realistic intraday target)
        day_end_price = current_price * 1.03
        day_end_pnl = (day_end_price - entry_price) * shares
        day_end_pct = ((day_end_price - entry_price) / entry_price) * 100
        
        return {
            'best_case': {
                'target_price': best_case_price,
                'potential_pnl': best_case_pnl,
                'potential_pnl_pct': best_case_pct,
                'description': '+10% upside scenario'
            },
            'worst_case': {
                'target_price': worst_case_price,
                'potential_pnl': worst_case_pnl,
                'potential_pnl_pct': worst_case_pct,
                'description': '-5% downside risk'
            },
            'day_end': {
                'target_price': day_end_price,
                'potential_pnl': day_end_pnl,
                'potential_pnl_pct': day_end_pct,
                'description': 'Realistic intraday target (+3%)'
            }
        }
    
    def _calculate_confidences(self, symbol: str, current_price: float, entry_price: float) -> dict:
        """Calculate day trade and long term confidence scores"""
        try:
            # Fetch recent data for analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            if df.empty or symbol not in df.index.get_level_values('symbol'):
                return {
                    'day_trade': {'score': 50, 'level': 'Medium'},
                    'long_term': {'score': 50, 'level': 'Medium'}
                }
            
            symbol_df = df.loc[symbol]
            
            # Day trade confidence based on recent volatility and momentum
            recent_returns = symbol_df['close'].pct_change().tail(5)
            volatility = recent_returns.std()
            momentum = recent_returns.mean()
            
            day_score = 50
            if volatility > 0.02 and momentum > 0:  # High volatility + positive momentum
                day_score += 30
            elif volatility > 0.02:  # High volatility
                day_score += 15
            if (current_price - entry_price) / entry_price > 0.01:  # Already profitable
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
                    'factors': f'Volatility: {volatility:.2%}, Momentum: {momentum:.2%}'
                },
                'long_term': {
                    'score': long_score,
                    'level': self._score_to_level(long_score),
                    'factors': f'Price vs MA20: {((current_price/ma_20 - 1) * 100):.1f}%'
                }
            }
        except Exception as e:
            print(f"Error calculating confidences for {symbol}: {e}")
            return {
                'day_trade': {'score': 50, 'level': 'Medium'},
                'long_term': {'score': 50, 'level': 'Medium'}
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
    
    def _reconstruct_entry_logic(self, position: dict, screening_model: str, daytrade_model: str) -> dict:
        """Reconstruct the logic that led to entering this trade"""
        # This would ideally be stored when the trade is made
        # For now, provide template logic based on models
        
        return {
            'screening_logic': self._get_screening_logic(screening_model),
            'entry_signal': self._get_entry_logic(daytrade_model),
            'timestamp': position.get('entry_time', datetime.now()).isoformat(),
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
    """Get latest price data for charting"""
    try:
        client = StockHistoricalDataClient(api_key, api_secret)
        
        # Get today's minute data
        end_date = datetime.now()
        start_date = datetime.combine(end_date.date(), datetime.min.time())
        
        request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Minute,
            start=start_date,
            end=end_date
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