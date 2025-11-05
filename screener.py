"""
Stock Screener
Filter stocks based on technical criteria
"""
from typing import List, Dict
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from statistics import fmean


class StockScreener:
    """Screen stocks based on technical criteria"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.client = StockHistoricalDataClient(api_key, api_secret)
    
    def get_movers(self, symbols: List[str], min_volume: int = 1000000) -> List[Dict]:
        """
        Get stocks with significant price movement and volume
        
        Args:
            symbols: List of symbols to screen
            min_volume: Minimum average volume threshold
            
        Returns:
            List of stocks with their metrics
        """
        movers = []
        
        # Get data for last 5 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            for symbol in symbols:
                try:
                    if symbol not in df.index.get_level_values('symbol'):
                        continue
                    
                    symbol_data = df.loc[symbol]
                    
                    if len(symbol_data) < 2:
                        continue
                    
                    # Calculate metrics
                    latest = symbol_data.iloc[-1]
                    previous = symbol_data.iloc[-2]
                    
                    price_change = (latest['close'] - previous['close']) / previous['close']
                    avg_volume = fmean(symbol_data['volume'].tolist())
                    
                    # Screen criteria
                    if abs(price_change) > 0.02 and avg_volume > min_volume:  # 2% move
                        movers.append({
                            'symbol': symbol,
                            'price': latest['close'],
                            'change_pct': price_change * 100,
                            'volume': latest['volume'],
                            'avg_volume': avg_volume,
                            'volume_ratio': latest['volume'] / avg_volume if avg_volume > 0 else 0
                        })
                
                except Exception as e:
                    print(f"Error screening {symbol}: {e}")
                    continue
            
            # Sort by absolute price change
            movers.sort(key=lambda x: abs(x['change_pct']), reverse=True)
            
        except Exception as e:
            print(f"Screening error: {e}")
        
        return movers
    
    def screen_momentum(self, symbols: List[str], lookback_days: int = 20) -> List[Dict]:
        """
        Screen for momentum stocks (price above moving average with high volume)
        
        Args:
            symbols: List of symbols to screen
            lookback_days: Number of days for moving average
            
        Returns:
            List of momentum stocks with metrics
        """
        momentum_stocks = []
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + 5)
        
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            for symbol in symbols:
                try:
                    if symbol not in df.index.get_level_values('symbol'):
                        continue
                    
                    symbol_data = df.loc[symbol]
                    
                    if len(symbol_data) < lookback_days:
                        continue
                    
                    # Calculate metrics
                    closes = symbol_data['close'].tolist()
                    volumes = symbol_data['volume'].tolist()
                    
                    latest_price = closes[-1]
                    sma = fmean(closes[-lookback_days:])
                    avg_volume = fmean(volumes[-lookback_days:])
                    
                    # Momentum criteria: price above SMA, recent volume increase
                    price_vs_sma = (latest_price - sma) / sma
                    volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 0
                    
                    if price_vs_sma > 0.02 and volume_ratio > 1.2:  # 2% above SMA, 20% volume increase
                        momentum_stocks.append({
                            'symbol': symbol,
                            'price': latest_price,
                            'sma': sma,
                            'price_vs_sma_pct': price_vs_sma * 100,
                            'volume': volumes[-1],
                            'avg_volume': avg_volume,
                            'volume_ratio': volume_ratio
                        })
                
                except Exception as e:
                    print(f"Error screening {symbol}: {e}")
                    continue
            
            # Sort by price vs SMA
            momentum_stocks.sort(key=lambda x: x['price_vs_sma_pct'], reverse=True)
            
        except Exception as e:
            print(f"Momentum screening error: {e}")
        
        return momentum_stocks
    
    def print_results(self, results: List[Dict], title: str = "Screening Results"):
        """Print screening results in a formatted table"""
        if not results:
            print(f"\n{title}: No stocks found")
            return
        
        print(f"\n{'='*80}")
        print(f"{title} ({len(results)} stocks)")
        print("="*80)
        
        for stock in results:
            print(f"\n{stock['symbol']}")
            for key, value in stock.items():
                if key != 'symbol':
                    if isinstance(value, float):
                        if 'pct' in key or 'ratio' in key:
                            print(f"  {key}: {value:.2f}")
                        else:
                            print(f"  {key}: ${value:,.2f}" if 'price' in key or 'volume' in key else f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")
        
        print("="*80)


if __name__ == "__main__":
    # Example usage
    import os
    from config import settings
    
    screener = StockScreener(settings.alpaca_key, settings.alpaca_secret)
    
    # Example symbols (you can expand this list)
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'NFLX', 'INTC']
    
    print("\n🔍 Screening stocks...")
    
    movers = screener.get_movers(symbols)
    screener.print_results(movers, "Top Movers")
    
    momentum = screener.screen_momentum(symbols)
    screener.print_results(momentum, "Momentum Stocks")