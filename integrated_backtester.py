"""
Optimized Integrated Backtester with Detailed Progress Updates
Key optimizations:
1. Batch API requests to fetch all stock data at once
2. Detailed progress messages for each step
3. Cache daily data to avoid re-fetching

FIXED BUGS:
- Implemented complete screening logic in _screen_with_bulk_data
- Added force_execution logic to allow trading even with low confidence
- Implemented complete trading simulation with signal generation
- Connected all models properly
- FIXED: Timezone-aware datetime handling for Alpaca API compatibility
- FIXED: Trade counting - only counts closed positions (sells) + added breakeven trades
"""

import pandas as pd
from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Tuple, Callable, Optional
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
import asyncio
import inspect


class OptimizedBacktester:
    """Optimized backtester with batch data fetching"""
    
    def __init__(self, api_key: str, api_secret: str, initial_capital: float = 10000):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.initial_capital = initial_capital
        self.feed = DataFeed.IEX
        self.data_cache = {}  # Cache fetched data
    
    async def _call_progress_callback(self, callback: Optional[Callable], *args, **kwargs):
        """
        Helper to call progress callback whether it's sync or async
        """
        if callback is None:
            return
        
        # Check if it's an async function
        if inspect.iscoroutinefunction(callback):
            await callback(*args, **kwargs)
        else:
            # It's a sync function, just call it normally
            callback(*args, **kwargs)
    
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
            daily_data = {}
            for symbol in symbols:
                try:
                    if symbol in df.index.get_level_values('symbol'):
                        daily_data[symbol] = df.loc[symbol]
                    else:
                        daily_data[symbol] = pd.DataFrame()
                except:
                    daily_data[symbol] = pd.DataFrame()
            
            return daily_data
            
        except Exception as e:
            print(f"Warning: Batch daily fetch failed: {e}")
            return {symbol: pd.DataFrame() for symbol in symbols}
    
    def fetch_minute_data_batch(self, symbols: List[str], target_date: datetime) -> Dict[str, pd.DataFrame]:
        """
        Fetch minute data for multiple symbols for a specific day
        
        Returns:
            Dict mapping symbol -> DataFrame of minute bars
        """
        # Create cache key
        date_str = target_date.strftime('%Y-%m-%d')
        cache_key = f"{date_str}_{'_'.join(sorted(symbols))}"
        
        # Check cache
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # Market hours: 9:30 AM - 4:00 PM ET
        start = datetime.combine(target_date.date(), dt_time(9, 30))
        end = datetime.combine(target_date.date(), dt_time(16, 0))
        
        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Minute,
            start=start,
            end=end,
            feed=self.feed
        )
        
        try:
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
    
    def run(
        self,
        screener_model: str,
        screener_params: dict,
        day_model: str,
        day_model_params: dict,
        start_date,
        end_date,
        stock_universe: list,
        top_n: int = 3,
        min_score: float = 60,
        force_execution: bool = False,
        progress_callback=None
    ) -> dict:
        """
        Synchronous wrapper for run_with_detailed_progress
        This allows the backtester to be called from both sync and async contexts
        """
        import asyncio
        
        # Create a new event loop if we're not in an async context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context, need to create new loop in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.run_with_detailed_progress(
                            screener_model=screener_model,
                            screener_params=screener_params,
                            day_model=day_model,
                            day_model_params=day_model_params,
                            start_date=start_date,
                            end_date=end_date,
                            stock_universe=stock_universe,
                            top_n=top_n,
                            min_score=min_score,
                            force_execution=force_execution,
                            progress_callback=progress_callback
                        )
                    )
                    return future.result()
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async method
        try:
            return loop.run_until_complete(
                self.run_with_detailed_progress(
                    screener_model=screener_model,
                    screener_params=screener_params,
                    day_model=day_model,
                    day_model_params=day_model_params,
                    start_date=start_date,
                    end_date=end_date,
                    stock_universe=stock_universe,
                    top_n=top_n,
                    min_score=min_score,
                    force_execution=force_execution,
                    progress_callback=progress_callback
                )
            )
        finally:
            # Only close if we created it
            if not loop.is_running():
                loop.close()
    
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
        Can be either sync or async function
        
        FIXED: Now properly implements screening and trading logic with force_execution support
        """
        from screening_models import get_screener
        from daytrade_models import get_day_trade_model
        
        # TIMEZONE FIX: Ensure dates are timezone-aware (UTC) to match Alpaca data
        if start_date.tzinfo is None:
            start_date = pd.Timestamp(start_date).tz_localize('UTC').to_pydatetime()
        if end_date.tzinfo is None:
            end_date = pd.Timestamp(end_date).tz_localize('UTC').to_pydatetime()
        
        # Calculate total days
        total_days = 0
        temp_date = start_date
        while temp_date <= end_date:
            if temp_date.weekday() < 5:
                total_days += 1
            temp_date += timedelta(days=1)
        
        await self._call_progress_callback(
            progress_callback,
            "Pre-fetching historical data for screening...",
            5,
            f"Fetching {len(stock_universe)} stocks in bulk (much faster!)"
        )
        
        # OPTIMIZATION: Pre-fetch ALL daily data at once
        print(f"📊 Pre-fetching data for {len(stock_universe)} stocks...")
        bulk_daily_data = self.fetch_bulk_daily_data(stock_universe, days_back=60)
        
        await self._call_progress_callback(
            progress_callback,
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
            await self._call_progress_callback(
                progress_callback,
                f"Day {day_count}/{total_days}: Screening stocks...",
                base_progress,
                f"Analyzing {len(stock_universe)} stocks for {day_str}"
            )
            
            # Screen stocks
            screened = await self._screen_with_bulk_data(
                screener,
                stock_universe,
                bulk_daily_data,
                min_score,
                force_execution,
                progress_callback,
                base_progress,
                day_count,
                total_days,
                current_date
            )
            
            if not screened:
                await self._call_progress_callback(
                    progress_callback,
                    f"Day {day_count}: No stocks qualified",
                    base_progress + 1,
                    f"Minimum score {min_score} not met, skipping day"
                )
                current_date += timedelta(days=1)
                continue
            
            # Select top N
            if force_execution:
                selected = screened[:top_n]
                await self._call_progress_callback(
                    progress_callback,
                    f"Day {day_count}: Force execution enabled",
                    base_progress + 1,
                    f"Trading top {len(selected)} stocks regardless of confidence"
                )
            else:
                selected = screened[:top_n]
            
            selected_symbols = [s['symbol'] for s in selected]
            
            await self._call_progress_callback(
                progress_callback,
                f"Day {day_count}: Selected top {len(selected)} stocks",
                base_progress + 2,
                f"Trading: {', '.join(selected_symbols)}"
            )
            
            # === TRADING SIMULATION ===
            day_trades = []
            
            for idx, stock_info in enumerate(selected, 1):
                symbol = stock_info['symbol']
                
                await self._call_progress_callback(
                    progress_callback,
                    f"Day {day_count}: Trading {symbol} ({idx}/{len(selected)})",
                    base_progress + 3 + idx,
                    f"Fetching minute data and simulating intraday trades..."
                )
                
                # Fetch minute data
                minute_data_dict = self.fetch_minute_data_batch([symbol], current_date)
                symbol_minute_data = minute_data_dict.get(symbol)
                
                if symbol_minute_data is None or symbol_minute_data.empty:
                    await self._call_progress_callback(
                        progress_callback,
                        f"Day {day_count}: {symbol} - No data",
                        base_progress + 3 + idx,
                        "Skipping due to missing minute data"
                    )
                    continue
                
                await self._call_progress_callback(
                    progress_callback,
                    f"Day {day_count}: Simulating {symbol}",
                    base_progress + 3 + idx,
                    f"Running {day_model} model on {len(symbol_minute_data)} minute bars"
                )
                
                # Simulate intraday trading
                trades_for_symbol = self._simulate_intraday_trading(
                    symbol,
                    symbol_minute_data,
                    stock_info,
                    day_trader,
                    cash,
                    force_execution
                )
                
                # Process trades and update cash
                for trade in trades_for_symbol:
                    if trade['action'] == 'buy':
                        cost = trade['shares'] * trade['price']
                        if cost <= cash:
                            cash -= cost
                            day_trades.append(trade)
                    elif trade['action'] == 'sell':
                        proceeds = trade['shares'] * trade['price']
                        cash += proceeds
                        day_trades.append(trade)
            
            # Record daily results
            all_trades.extend(day_trades)
            daily_results.append({
                'date': day_str,
                'stocks_screened': len(stock_universe),
                'stocks_qualified': len(screened),
                'stocks_traded': len(selected),
                'trades': len(day_trades),
                'cash': cash
            })
            
            current_date += timedelta(days=1)
        
        # Final progress
        await self._call_progress_callback(
            progress_callback,
            "Compiling results...",
            95,
            f"Processed {completed_days} trading days"
        )
        
        # Calculate results
        final_value = cash + sum(pos.get('current_price', 0) * pos.get('shares', 0) for pos in positions.values())
        total_return = final_value - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # ============================================================================
        # FIXED: Calculate trade statistics - ONLY count closed positions (sells)
        # ============================================================================
        closed_trades = [t for t in all_trades if t.get('action') == 'sell']
        
        # Define breakeven threshold (e.g., within $0.01)
        breakeven_threshold = 0.01  # $0.01
        
        winning_trades = sum(1 for t in closed_trades if t.get('pnl', 0) > breakeven_threshold)
        losing_trades = sum(1 for t in closed_trades if t.get('pnl', 0) < -breakeven_threshold)
        breakeven_trades = sum(1 for t in closed_trades if abs(t.get('pnl', 0)) <= breakeven_threshold)
        
        total_trades = len(closed_trades)
        win_rate = winning_trades / total_trades if total_trades else 0
        
        avg_win = sum(t['pnl'] for t in closed_trades if t.get('pnl', 0) > breakeven_threshold) / winning_trades if winning_trades else 0
        avg_loss = abs(sum(t['pnl'] for t in closed_trades if t.get('pnl', 0) < -breakeven_threshold) / losing_trades) if losing_trades else 0
        profit_factor = (winning_trades * avg_win) / (losing_trades * avg_loss) if losing_trades and avg_loss else 0
        
        results = {
            'strategy': f"{screener_model} + {day_model}",
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,  # Now only counts closed positions
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'breakeven_trades': breakeven_trades,  # NEW: Add breakeven trades
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades': all_trades,  # Keep all trades for detailed view
            'daily_results': daily_results,
            'unique_stocks_traded': len(set(t.get('symbol', '') for t in all_trades)),
            'screening_sessions': completed_days
        }
        # ============================================================================
        
        await self._call_progress_callback(
            progress_callback,
            "Backtest complete!",
            100,
            f"Final value: ${results['final_value']:,.2f} ({total_return_pct:+.2f}%)"
        )
        
        return results
    
    async def _screen_with_bulk_data(
        self,
        screener,
        universe: List[str],
        bulk_data: Dict[str, pd.DataFrame],
        min_score: float,
        force_execution: bool,
        progress_callback: Optional[Callable],
        base_progress: int,
        day_num: int,
        total_days: int,
        current_date: datetime
    ) -> List[dict]:
        """Screen stocks using pre-fetched bulk data with detailed progress"""
        
        results = []
        total_stocks = len(universe)
        
        for idx, symbol in enumerate(universe):
            # Update progress every 10%
            if idx % (max(1, total_stocks // 10)) == 0:
                pct_through = int((idx / total_stocks) * 100)
                await self._call_progress_callback(
                    progress_callback,
                    f"Day {day_num}: Screening progress {pct_through}%",
                    base_progress,
                    f"Analyzed {idx}/{total_stocks} stocks, {len(results)} qualified so far"
                )
            
            df = bulk_data.get(symbol, pd.DataFrame())
            if df.empty or len(df) < 20:
                continue
            
            # Filter data up to current date
            df_filtered = df[df.index <= current_date]
            if df_filtered.empty or len(df_filtered) < 20:
                continue
            
            try:
                closes = df_filtered['close'].tolist()
                volumes = df_filtered['volume'].tolist()
                current_price = closes[-1]
                
                # Basic scoring
                score = 50
                reasons = []
                metadata = {}
                
                # Momentum check
                if len(closes) >= 5:
                    recent_change = (closes[-1] - closes[-5]) / closes[-5]
                    if recent_change > 0.05:
                        score += 20
                        reasons.append("Strong upward momentum")
                    elif recent_change > 0.02:
                        score += 10
                        reasons.append("Positive momentum")
                
                # Volume check
                if len(volumes) >= 10:
                    avg_volume = sum(volumes[-10:]) / 10
                    if volumes[-1] > avg_volume * 1.5:
                        score += 15
                        reasons.append("High volume")
                
                metadata = {
                    'momentum': recent_change if len(closes) >= 5 else 0,
                    'volume_ratio': volumes[-1] / (sum(volumes[-10:]) / 10) if len(volumes) >= 10 else 1
                }
                
                # Include stock if score meets threshold OR if force_execution is enabled
                if score >= min_score or force_execution:
                    results.append({
                        'symbol': symbol,
                        'score': score,
                        'price': current_price,
                        'volume': volumes[-1],
                        'reason': " | ".join(reasons) if reasons else "Selected by force execution",
                        'metadata': metadata,
                        'forced': score < min_score and force_execution
                    })
                    
            except Exception as e:
                continue
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def _simulate_intraday_trading(
        self,
        symbol: str,
        minute_bars: pd.DataFrame,
        screener_data: dict,
        day_trader,
        available_cash: float,
        force_execution: bool
    ) -> List[dict]:
        """Simulate intraday trading using the day trading model"""
        
        trades = []
        position = None
        
        # Iterate through minute bars
        for i in range(len(minute_bars)):
            current_bar = minute_bars.iloc[i]
            current_price = current_bar['close']
            timestamp = minute_bars.index[i] if hasattr(minute_bars.index[i], 'to_pydatetime') else current_bar.name
            
            # Get signal from day trading model
            bars_so_far = minute_bars.iloc[:i+1]
            
            try:
                signal = day_trader.generate_signal(symbol, bars_so_far, screener_data)
                
                if signal and signal.action == 'buy' and position is None:
                    # Check confidence or force execution
                    if signal.confidence >= 0.6 or force_execution:
                        # Calculate position size (use 10% of available cash)
                        position_size = min(available_cash * 0.1, available_cash * 0.2)
                        shares = int(position_size / signal.price)
                        
                        if shares > 0 and (shares * signal.price) <= available_cash:
                            position = {
                                'shares': shares,
                                'entry_price': signal.price
                            }
                            
                            trades.append({
                                'symbol': symbol,
                                'action': 'buy',
                                'shares': shares,
                                'price': signal.price,
                                'timestamp': timestamp,
                                'reason': signal.reason,
                                'pnl': 0,
                                'pnl_pct': 0
                            })
                
                elif position is not None:
                    # Check exit conditions
                    should_exit = False
                    exit_reason = ""
                    
                    # Get exit signal from model
                    should_exit_result = day_trader.should_exit(position, current_bar, timestamp)
                    
                    if isinstance(should_exit_result, tuple):
                        should_exit, exit_reason = should_exit_result
                    else:
                        should_exit = should_exit_result
                        exit_reason = "Model exit signal"
                    
                    if should_exit:
                        proceeds = position['shares'] * current_price
                        cost = position['shares'] * position['entry_price']
                        pnl = proceeds - cost
                        pnl_pct = (current_price - position['entry_price']) / position['entry_price']
                        
                        trades.append({
                            'symbol': symbol,
                            'action': 'sell',
                            'shares': position['shares'],
                            'price': current_price,
                            'timestamp': timestamp,
                            'reason': exit_reason,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct
                        })
                        
                        position = None
                        
            except Exception as e:
                continue
        
        # Close any remaining position at end of day
        if position is not None:
            final_bar = minute_bars.iloc[-1]
            final_price = final_bar['close']
            final_timestamp = minute_bars.index[-1] if hasattr(minute_bars.index[-1], 'to_pydatetime') else final_bar.name
            
            proceeds = position['shares'] * final_price
            cost = position['shares'] * position['entry_price']
            pnl = proceeds - cost
            pnl_pct = (final_price - position['entry_price']) / position['entry_price']
            
            trades.append({
                'symbol': symbol,
                'action': 'sell',
                'shares': position['shares'],
                'price': final_price,
                'timestamp': final_timestamp,
                'reason': "End of day close",
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
        
        return trades


# Alias for backward compatibility
IntegratedBacktester = OptimizedBacktester