"""
Optimized Integrated Backtester with Detailed Progress Updates
Key optimizations:
1. Batch API requests to fetch all stock data at once
2. Detailed progress messages for each step
3. Cache daily data to avoid re-fetching
"""

import pandas as pd
from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Tuple, Callable, Optional
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
import asyncio


class OptimizedBacktester:
    """Optimized backtester with batch data fetching"""
    
    def __init__(self, api_key: str, api_secret: str, initial_capital: float = 10000):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.initial_capital = initial_capital
        self.feed = DataFeed.IEX
        self.data_cache = {}  # Cache fetched data
    
    def fetch_bulk_daily_data(self, symbols: List[str], days_back: int = 60) -> Dict[str, pd.DataFrame]:
        """
        Fetch daily data for ALL symbols at once (much faster than individual calls)
        
        Returns:
            Dict mapping symbol -> DataFrame of daily bars
        """
        end = datetime.now()
        start = end - timedelta(days=days_back)
        
        # Batch request for ALL symbols at once
        request = StockBarsRequest(
            symbol_or_symbols=symbols,  # All symbols in one request!
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            feed=self.feed
        )
        
        try:
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            # Organize by symbol
            data = {}
            for symbol in symbols:
                try:
                    if symbol in df.index.get_level_values('symbol'):
                        data[symbol] = df.loc[symbol]
                    else:
                        data[symbol] = pd.DataFrame()
                except:
                    data[symbol] = pd.DataFrame()
            
            return data
        except Exception as e:
            print(f"Warning: Bulk fetch failed: {e}")
            return {symbol: pd.DataFrame() for symbol in symbols}
    
    def fetch_minute_data_batch(self, symbols: List[str], date: datetime) -> Dict[str, pd.DataFrame]:
        """
        Fetch minute data for multiple symbols at once
        Much faster than individual requests
        """
        start = datetime.combine(date.date(), dt_time(9, 30))
        end = datetime.combine(date.date(), dt_time(16, 0))
        
        # Check cache first
        cache_key = f"{date.date()}_{'-'.join(sorted(symbols))}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        try:
            # Single batched request for all symbols
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Minute,
                start=start,
                end=end,
                feed=self.feed
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            # Organize by symbol
            minute_data = {}
            for symbol in symbols:
                try:
                    if symbol in df.index.get_level_values('symbol'):
                        minute_data[symbol] = df.loc[symbol]
                    else:
                        minute_data[symbol] = pd.DataFrame()
                except:
                    minute_data[symbol] = pd.DataFrame()
            
            # Cache it
            self.data_cache[cache_key] = minute_data
            return minute_data
            
        except Exception as e:
            print(f"Warning: Batch minute fetch failed: {e}")
            return {symbol: pd.DataFrame() for symbol in symbols}
    
    async def run_with_detailed_progress(
        self,
        screener_model: str,
        screener_params: dict,
        day_model: str,
        day_model_params: dict,
        start_date: datetime,
        end_date: datetime,
        stock_universe: List[str],
        top_n: int = 3,
        min_score: float = 60,
        force_execution: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        Run backtest with extremely detailed progress updates
        
        Progress callback receives: (message, progress_pct, detail)
        """
        from screening_models import get_screener
        from daytrade_models import get_day_trade_model
        
        # Calculate total days
        total_days = 0
        temp_date = start_date
        while temp_date <= end_date:
            if temp_date.weekday() < 5:
                total_days += 1
            temp_date += timedelta(days=1)
        
        if progress_callback:
            await progress_callback(
                "Pre-fetching historical data for screening...",
                5,
                f"Fetching {len(stock_universe)} stocks in bulk (much faster!)"
            )
        
        # OPTIMIZATION: Pre-fetch ALL daily data at once
        print(f"📊 Pre-fetching data for {len(stock_universe)} stocks...")
        bulk_daily_data = self.fetch_bulk_daily_data(stock_universe, days_back=60)
        
        if progress_callback:
            await progress_callback(
                "Data pre-fetch complete!",
                10,
                f"Successfully loaded data for screening"
            )
        
        # Initialize
        cash = self.initial_capital
        positions = {}
        all_trades = []
        daily_results = []
        
        # Create models
        screener = get_screener(screener_model, self.api_key, self.api_secret, **screener_params)
        day_trader = get_day_trade_model(day_model, **day_model_params)
        
        # Iterate through trading days
        current_date = start_date
        day_count = 0
        completed_days = 0
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            day_count += 1
            completed_days += 1
            base_progress = 10 + int((completed_days / total_days) * 85)  # 10-95%
            
            day_str = current_date.strftime("%Y-%m-%d")
            
            # === SCREENING PHASE ===
            if progress_callback:
                await progress_callback(
                    f"Day {day_count}/{total_days}: Screening stocks...",
                    base_progress,
                    f"Analyzing {len(stock_universe)} stocks for {day_str}"
                )
            
            # Screen with pre-fetched data
            screened = await self._screen_with_bulk_data(
                screener,
                stock_universe,
                bulk_daily_data,
                min_score,
                progress_callback,
                base_progress,
                day_count,
                total_days
            )
            
            if not screened:
                if progress_callback:
                    await progress_callback(
                        f"Day {day_count}: No stocks qualified",
                        base_progress + 1,
                        f"Minimum score {min_score} not met, skipping day"
                    )
                current_date += timedelta(days=1)
                continue
            
            # Select top N
            selected = screened[:top_n]
            selected_symbols = [s['symbol'] for s in selected]
            
            if progress_callback:
                await progress_callback(
                    f"Day {day_count}: Selected top {len(selected)} stocks",
                    base_progress + 2,
                    f"Trading: {', '.join(selected_symbols)}"
                )
            
            # === RANKING DISPLAY ===
            if progress_callback:
                ranking_detail = "\n".join([
                    f"#{i+1}: {s['symbol']} (Score: {s['score']:.1f}) - {s.get('reason', 'N/A')[:50]}"
                    for i, s in enumerate(selected)
                ])
                await progress_callback(
                    f"Day {day_count}: Stock rankings",
                    base_progress + 3,
                    ranking_detail
                )
            
            # === TRADING SIMULATION ===
            for idx, stock_info in enumerate(selected, 1):
                symbol = stock_info['symbol']
                
                if progress_callback:
                    await progress_callback(
                        f"Day {day_count}: Trading {symbol} ({idx}/{len(selected)})",
                        base_progress + 3 + idx,
                        f"Fetching minute data and simulating intraday trades..."
                    )
                
                # Fetch minute data (will use cache if available)
                minute_data_dict = self.fetch_minute_data_batch([symbol], current_date)
                symbol_minute_data = minute_data_dict.get(symbol)
                
                if symbol_minute_data is None or symbol_minute_data.empty:
                    if progress_callback:
                        await progress_callback(
                            f"Day {day_count}: {symbol} - No data",
                            base_progress + 4 + idx,
                            "Skipping due to missing minute data"
                        )
                    continue
                
                # Simulate trading for this stock
                if progress_callback:
                    await progress_callback(
                        f"Day {day_count}: Simulating {symbol}",
                        base_progress + 4 + idx,
                        f"Running {day_model} model on {len(symbol_minute_data)} minute bars"
                    )
                
                # (Rest of trading simulation logic here...)
                # This would include the actual day trading simulation
            
            current_date += timedelta(days=1)
        
        # Final progress
        if progress_callback:
            await progress_callback(
                "Compiling results...",
                95,
                f"Processed {completed_days} trading days"
            )
        
        # Calculate results
        results = {
            'initial_capital': self.initial_capital,
            'final_value': cash + sum(pos['current_price'] * pos['shares'] for pos in positions.values()),
            'trades': all_trades,
            'daily_results': daily_results
        }
        
        if progress_callback:
            await progress_callback(
                "Backtest complete!",
                100,
                f"Final value: ${results['final_value']:,.2f}"
            )
        
        return results
    
    async def _screen_with_bulk_data(
        self,
        screener,
        universe: List[str],
        bulk_data: Dict[str, pd.DataFrame],
        min_score: float,
        progress_callback: Optional[Callable],
        base_progress: int,
        day_num: int,
        total_days: int
    ) -> List[dict]:
        """Screen stocks using pre-fetched bulk data with detailed progress"""
        
        results = []
        total_stocks = len(universe)
        
        for idx, symbol in enumerate(universe):
            # Update progress every 10%
            if idx % (max(1, total_stocks // 10)) == 0:
                pct_through = int((idx / total_stocks) * 100)
                if progress_callback:
                    await progress_callback(
                        f"Day {day_num}: Screening progress {pct_through}%",
                        base_progress,
                        f"Analyzed {idx}/{total_stocks} stocks, {len(results)} qualified so far"
                    )
            
            df = bulk_data.get(symbol, pd.DataFrame())
            if df.empty:
                continue
            
            # Run screening logic with cached data
            # (Screening logic here - use df instead of fetching)
        
        return sorted(results, key=lambda x: x['score'], reverse=True)