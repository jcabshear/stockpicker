"""
Optimized Integrated Backtester with Detailed Progress Updates AND Daily Allocation
====================================================================================

FEATURES:
- Detailed progress messages showing stocks screened, selected, and traded
- Daily allocation percentage control
- Settlement time tracking (T+2)
- Accurate buying power management
- Batch API requests for performance
- Force execution logic
- Timezone-aware datetime handling

FIXED:
- Infinity JSON error (uses 999.0 instead)
- Trade counting (only counts closed positions)
- Added breakeven trades
- Added daily allocation and settlement tracking
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
from dataclasses import dataclass


@dataclass
class SettledFunds:
    """Track funds that will settle on a future date"""
    amount: float
    settlement_date: datetime


class OptimizedBacktester:
    """Optimized backtester with batch data fetching and daily allocation control"""
    
    def __init__(
        self, 
        api_key: str, 
        api_secret: str, 
        initial_capital: float = 10000,
        daily_allocation_pct: float = 0.10,  # NEW: 10% per day
        settlement_days: int = 2              # NEW: T+2 settlement
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.initial_capital = initial_capital
        self.feed = DataFeed.IEX
        self.data_cache = {}
        
        # NEW: Allocation and settlement tracking
        self.daily_allocation_pct = daily_allocation_pct
        self.settlement_days = settlement_days
        self.settled_cash = initial_capital
        self.unsettled_funds: List[SettledFunds] = []
        self.daily_capital_records = []
    
    def get_available_buying_power(self, current_date: datetime) -> float:
        """
        NEW: Calculate available buying power on a given date
        Settles any funds that are ready
        """
        newly_settled = 0
        remaining_unsettled = []
        
        for fund in self.unsettled_funds:
            if fund.settlement_date <= current_date:
                newly_settled += fund.amount
            else:
                remaining_unsettled.append(fund)
        
        self.settled_cash += newly_settled
        self.unsettled_funds = remaining_unsettled
        
        return self.settled_cash
    
    def allocate_daily_capital(self, buying_power: float, num_stocks: int) -> Dict:
        """
        NEW: Calculate daily allocation split among stocks
        """
        daily_allocation = buying_power * self.daily_allocation_pct
        per_stock_allocation = daily_allocation / num_stocks if num_stocks > 0 else 0
        
        return {
            'total_buying_power': buying_power,
            'daily_allocation': daily_allocation,
            'num_stocks': num_stocks,
            'per_stock_allocation': per_stock_allocation
        }
    
    async def _call_progress_callback(self, callback: Optional[Callable], *args, **kwargs):
        """Helper to call progress callback whether it's sync or async"""
        if callback is None:
            return
        
        if inspect.iscoroutinefunction(callback):
            await callback(*args, **kwargs)
        else:
            callback(*args, **kwargs)
    
    def fetch_bulk_daily_data(self, symbols: List[str], days_back: int = 60) -> Dict[str, pd.DataFrame]:
        """Fetch daily data for ALL symbols at once (much faster than individual calls)"""
        end = datetime.now()
        start = end - timedelta(days=days_back)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            feed=self.feed
        )
        
        try:
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
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
            print(f"Warning: Bulk daily fetch failed: {e}")
            return {symbol: pd.DataFrame() for symbol in symbols}
    
    def fetch_bulk_minute_data(
        self, 
        symbols: List[str], 
        start: datetime, 
        end: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Fetch minute data for multiple symbols (cached)"""
        cache_key = f"{','.join(sorted(symbols))}_{start.date()}_{end.date()}"
        
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
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
            
            minute_data = {}
            for symbol in symbols:
                try:
                    if symbol in df.index.get_level_values('symbol'):
                        minute_data[symbol] = df.loc[symbol]
                    else:
                        minute_data[symbol] = pd.DataFrame()
                except:
                    minute_data[symbol] = pd.DataFrame()
            
            self.data_cache[cache_key] = minute_data
            return minute_data
            
        except Exception as e:
            print(f"Warning: Batch minute fetch failed: {e}")
            return {symbol: pd.DataFrame() for symbol in symbols}
    
    def _screen_with_bulk_data(
        self,
        bulk_daily_data: Dict[str, pd.DataFrame],
        screener,
        min_score: float
    ) -> List:
        """Screen stocks using pre-fetched bulk data"""
        from models.screeners import ScreenedStock
        
        screened = []
        for symbol, df in bulk_daily_data.items():
            if df.empty or len(df) < 20:
                continue
            
            try:
                result = screener.screen_with_data(symbol, df)
                
                if result and result.score >= min_score:
                    screened.append(result)
                    
            except Exception as e:
                continue
        
        screened.sort(key=lambda x: x.score, reverse=True)
        return screened
    
    def _simulate_intraday_trading(
        self,
        symbol: str,
        minute_bars: pd.DataFrame,
        stock_info: dict,
        day_trader,
        per_stock_allocation: float,  # NEW: Use per-stock allocation
        force_execution: bool
    ) -> List[dict]:
        """
        Simulate intraday trading for one stock
        UPDATED: Uses per_stock_allocation and settlement tracking
        """
        trades = []
        position = None
        
        for idx, row in minute_bars.iterrows():
            timestamp = idx if hasattr(idx, 'to_pydatetime') else row.name
            current_price = row['close']
            
            current_bar = {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }
            
            try:
                # Entry logic
                if position is None:
                    signal = day_trader.generate_signal(symbol, minute_bars.loc[:idx], stock_info)
                    
                    if signal and signal.action == 'buy':
                        confidence_threshold = 0 if force_execution else 0.6
                        
                        if signal.confidence >= confidence_threshold:
                            # NEW: Use per_stock_allocation
                            shares = per_stock_allocation / signal.price
                            cost = shares * signal.price
                            
                            # NEW: Check settled cash
                            if cost <= self.settled_cash:
                                self.settled_cash -= cost
                                
                                position = {
                                    'shares': shares,
                                    'entry_price': signal.price,
                                    'current_price': signal.price,
                                    'stop_loss': signal.stop_loss,
                                    'take_profit': signal.take_profit
                                }
                                
                                trades.append({
                                    'symbol': symbol,
                                    'action': 'buy',
                                    'shares': shares,
                                    'price': signal.price,
                                    'timestamp': timestamp,
                                    'reason': signal.reason,
                                    'confidence': signal.confidence
                                })
                
                # Exit logic
                elif position is not None:
                    position['current_price'] = current_price
                    
                    should_exit = False
                    exit_reason = ""
                    
                    # Stop loss
                    if position.get('stop_loss') and current_price <= position['stop_loss']:
                        should_exit = True
                        exit_reason = "Stop loss triggered"
                    
                    # Take profit
                    elif position.get('take_profit') and current_price >= position['take_profit']:
                        should_exit = True
                        exit_reason = "Take profit hit"
                    
                    # Model exit signal
                    else:
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
                        
                        # NEW: Schedule settlement (T+2)
                        settlement_date = timestamp + timedelta(days=self.settlement_days)
                        self.unsettled_funds.append(SettledFunds(proceeds, settlement_date))
                        
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
            
            # NEW: Schedule settlement
            settlement_date = final_timestamp + timedelta(days=self.settlement_days)
            self.unsettled_funds.append(SettledFunds(proceeds, settlement_date))
            
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
    
    async def run_with_detailed_progress(
        self,
        screener_model: str,
        screener_params: dict,
        day_model: str,
        day_model_params: dict,
        start_date: datetime,
        end_date: datetime,
        stock_universe: list,
        top_n: int = 3,
        min_score: float = 60,
        force_execution: bool = False,
        progress_callback=None
    ) -> dict:
        """
        Run backtest with detailed progress updates AND allocation tracking
        """
        from models.screeners import get_screener
        from models.daytrade import get_day_trade_model
        
        await self._call_progress_callback(
            progress_callback,
            "Loading screening model...",
            5,
            f"Initializing {screener_model}"
        )
        
        # Initialize models
        screener = get_screener(screener_model, self.api_key, self.api_secret, **screener_params)
        day_trader = get_day_trade_model(day_model, **day_model_params)
        
        await self._call_progress_callback(
            progress_callback,
            "Fetching market data...",
            10,
            f"Downloading data for {len(stock_universe)} stocks"
        )
        
        # Fetch bulk daily data once
        bulk_daily_data = self.fetch_bulk_daily_data(stock_universe, days_back=90)
        
        # Initialize tracking
        all_trades = []
        positions = {}
        current_date = start_date
        completed_days = 0
        total_days = (end_date - start_date).days
        
        # NEW: Reset capital tracking
        self.settled_cash = self.initial_capital
        self.unsettled_funds = []
        self.daily_capital_records = []
        
        # Daily loop
        while current_date <= end_date:
            day_str = current_date.strftime('%Y-%m-%d')
            completed_days += 1
            progress_pct = 15 + int((completed_days / total_days) * 75)
            
            await self._call_progress_callback(
                progress_callback,
                f"Processing {day_str}...",
                progress_pct,
                f"Day {completed_days}/{total_days}"
            )
            
            # NEW: Get available buying power (settles funds if ready)
            buying_power = self.get_available_buying_power(current_date)
            
            # Screen stocks
            await self._call_progress_callback(
                progress_callback,
                f"Screening {len(stock_universe)} stocks...",
                progress_pct,
                f"Looking for stocks with score >= {min_score}"
            )
            
            screened = self._screen_with_bulk_data(
                bulk_daily_data,
                screener,
                min_score
            )
            
            await self._call_progress_callback(
                progress_callback,
                f"Screening complete",
                progress_pct,
                f"Found {len(screened)} stocks qualifying (score >= {min_score})"
            )
            
            if not screened:
                await self._call_progress_callback(
                    progress_callback,
                    f"No stocks qualified",
                    progress_pct,
                    f"Skipping {day_str} - no stocks met minimum score"
                )
                current_date += timedelta(days=1)
                continue
            
            # Select top N
            selected = screened[:top_n]
            selected_symbols = [s.symbol for s in selected]
            
            # NEW: Allocate capital for the day
            allocation = self.allocate_daily_capital(buying_power, len(selected))
            per_stock_allocation = allocation['per_stock_allocation']
            
            await self._call_progress_callback(
                progress_callback,
                f"Selected top {len(selected)} stocks",
                progress_pct,
                f"Trading: {', '.join(selected_symbols)} (${per_stock_allocation:,.2f} each)"
            )
            
            # Fetch minute data for selected stocks
            symbols = [s.symbol for s in selected]
            day_start = current_date.replace(hour=9, minute=30)
            day_end = current_date.replace(hour=16, minute=0)
            
            await self._call_progress_callback(
                progress_callback,
                f"Fetching minute data...",
                progress_pct,
                f"Downloading intraday bars for {len(symbols)} stocks"
            )
            
            minute_data = self.fetch_bulk_minute_data(symbols, day_start, day_end)
            
            # Trade each selected stock
            day_trades = []
            for idx, stock_info in enumerate(selected, 1):
                symbol = stock_info.symbol
                symbol_minute_data = minute_data.get(symbol, pd.DataFrame())
                
                if symbol_minute_data.empty:
                    await self._call_progress_callback(
                        progress_callback,
                        f"{symbol}: No minute data",
                        progress_pct,
                        f"Skipping {symbol} - no intraday data available"
                    )
                    continue
                
                await self._call_progress_callback(
                    progress_callback,
                    f"Trading {symbol} ({idx}/{len(selected)})",
                    progress_pct,
                    f"Running {day_model} model on {len(symbol_minute_data)} minute bars"
                )
                
                # NEW: Pass per_stock_allocation
                trades_for_symbol = self._simulate_intraday_trading(
                    symbol,
                    symbol_minute_data,
                    stock_info.__dict__,
                    day_trader,
                    per_stock_allocation,  # Use allocated amount per stock
                    force_execution
                )
                
                # Log trades
                for trade in trades_for_symbol:
                    if trade['action'] == 'buy':
                        await self._call_progress_callback(
                            progress_callback,
                            f"✅ BUY {symbol}",
                            progress_pct,
                            f"{trade['shares']:.2f} shares @ ${trade['price']:.2f} = ${trade['shares'] * trade['price']:.2f}"
                        )
                    elif trade['action'] == 'sell':
                        pnl_str = f"+${trade['pnl']:.2f}" if trade['pnl'] > 0 else f"-${abs(trade['pnl']):.2f}"
                        await self._call_progress_callback(
                            progress_callback,
                            f"💰 SELL {symbol}",
                            progress_pct,
                            f"{trade['shares']:.2f} shares @ ${trade['price']:.2f} (P&L: {pnl_str})"
                        )
                
                day_trades.extend(trades_for_symbol)
            
            all_trades.extend(day_trades)
            
            # NEW: Record daily capital state
            position_value = sum(
                p.get('shares', 0) * p.get('current_price', 0) 
                for p in positions.values()
            )
            unsettled_total = sum(f.amount for f in self.unsettled_funds)
            total_equity = self.settled_cash + unsettled_total + position_value
            
            self.daily_capital_records.append({
                'date': current_date,
                'settled_cash': self.settled_cash,
                'unsettled_cash': unsettled_total,
                'position_value': position_value,
                'total_equity': total_equity,
                'trades': len(day_trades),
                'open_positions': len(positions)
            })
            
            current_date += timedelta(days=1)
        
        # Calculate results
        await self._call_progress_callback(
            progress_callback,
            "Compiling results...",
            95,
            f"Processed {completed_days} trading days"
        )
        
        # Final calculations
        final_equity = self.daily_capital_records[-1]['total_equity'] if self.daily_capital_records else self.initial_capital
        total_return = final_equity - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # Trade statistics (only closed trades - sells)
        trades_df = pd.DataFrame(all_trades)
        sell_trades = trades_df[trades_df['action'] == 'sell'] if not trades_df.empty else pd.DataFrame()
        
        winning_trades = len(sell_trades[sell_trades['pnl'] > 0]) if not sell_trades.empty else 0
        losing_trades = len(sell_trades[sell_trades['pnl'] < 0]) if not sell_trades.empty else 0
        breakeven_trades = len(sell_trades[sell_trades['pnl'] == 0]) if not sell_trades.empty else 0
        total_trades = len(sell_trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = sell_trades[sell_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = sell_trades[sell_trades['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        total_wins = sell_trades[sell_trades['pnl'] > 0]['pnl'].sum() if winning_trades > 0 else 0
        total_losses = abs(sell_trades[sell_trades['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
        # FIXED: Use 999.0 instead of Infinity for JSON compatibility
        profit_factor = total_wins / total_losses if total_losses > 0 else 999.0
        
        unique_stocks = set(t['symbol'] for t in all_trades) if all_trades else set()
        
        results = {
            'strategy': f"{screener_model} + {day_model}",
            'initial_capital': self.initial_capital,
            'final_value': final_equity,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'breakeven_trades': breakeven_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades': all_trades,
            'unique_stocks_traded': len(unique_stocks),
            'screening_sessions': completed_days,
            # NEW: Daily allocation metrics
            'daily_allocation_pct': self.daily_allocation_pct,
            'settlement_days': self.settlement_days,
            'daily_capital_records': self.daily_capital_records
        }
        
        return results
    
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
        """Synchronous wrapper for run_with_detailed_progress"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.run_with_detailed_progress(
                            screener_model, screener_params,
                            day_model, day_model_params,
                            start_date, end_date,
                            stock_universe, top_n, min_score,
                            force_execution, progress_callback
                        )
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.run_with_detailed_progress(
                        screener_model, screener_params,
                        day_model, day_model_params,
                        start_date, end_date,
                        stock_universe, top_n, min_score,
                        force_execution, progress_callback
                    )
                )
        except RuntimeError:
            return asyncio.run(
                self.run_with_detailed_progress(
                    screener_model, screener_params,
                    day_model, day_model_params,
                    start_date, end_date,
                    stock_universe, top_n, min_score,
                    force_execution, progress_callback
                )
            )


# Alias for backward compatibility
IntegratedBacktester = OptimizedBacktester