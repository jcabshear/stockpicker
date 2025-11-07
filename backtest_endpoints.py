"""
Backtest API Endpoints Module
Includes SSE streaming for real-time progress updates
UNIVERSAL VERSION: Works with both IntegratedBacktester and OptimizedBacktester
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, AsyncGenerator
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import settings
from stock_universe import get_full_universe

# Try to import either class name
try:
    from integrated_backtester import IntegratedBacktester as Backtester
except ImportError:
    try:
        from integrated_backtester import OptimizedBacktester as Backtester
    except ImportError:
        raise ImportError("Could not import backtester class. Please ensure integrated_backtester.py contains either IntegratedBacktester or OptimizedBacktester class.")

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["backtest"])


class ComprehensiveBacktestParams(BaseModel):
    """Parameters for comprehensive backtest"""
    screener_model: str
    screener_params: dict
    day_model: str
    day_model_params: dict
    top_n_stocks: int
    min_score: float
    force_execution: bool
    days: int
    initial_capital: float
    stock_universe: Optional[List[str]] = None


# ============================================================================
# SSE STREAMING ENDPOINT (Real-time Progress)
# ============================================================================

@router.get("/comprehensive-backtest-stream")
async def comprehensive_backtest_stream(
    screener_model: str = Query(...),
    day_model: str = Query(...),
    top_n_stocks: int = Query(...),
    min_score: float = Query(...),
    days: int = Query(...),
    initial_capital: float = Query(...),
    force_execution: bool = Query(False),
    stock_universe: Optional[str] = Query(None)
):
    """
    Stream comprehensive backtest progress using Server-Sent Events (SSE)
    Provides real-time updates as the backtest runs
    """
    
    async def generate_progress() -> AsyncGenerator[str, None]:
        """Generate SSE progress updates"""
        try:
            # Initial connection
            yield f"data: {json.dumps({'type': 'progress', 'percent': 0, 'message': 'Initializing backtester...', 'detail': 'Loading configuration and models'})}\n\n"
            await asyncio.sleep(0.1)
            
            logger.info(f"🚀 Starting SSE backtest: {screener_model} + {day_model}")
            
            # Create backtester using the imported class (works with either name)
            backtester = Backtester(
                api_key=settings.alpaca_key,
                api_secret=settings.alpaca_secret,
                initial_capital=initial_capital
            )
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get stock universe
            if stock_universe:
                universe = stock_universe.split(',')
            elif screener_model == 'manual':
                raise HTTPException(400, "Manual selection requires stock_universe parameter")
            else:
                universe = get_full_universe()
            
            yield f"data: {json.dumps({'type': 'progress', 'percent': 2, 'message': f'Universe: {len(universe)} stocks', 'detail': f'Backtesting from {start_date.date()} to {end_date.date()}'})}\n\n"
            await asyncio.sleep(0.1)
            
            logger.info(f"📊 Backtest params: {days} days, {len(universe)} stocks, top {top_n_stocks}")
            
            yield f"data: {json.dumps({'type': 'progress', 'percent': 5, 'message': 'Starting backtest...', 'detail': 'Initializing models and preparing data'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Run backtest in thread pool to avoid blocking
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            # Create a queue for progress updates
            progress_queue = asyncio.Queue()
            
            def sync_progress_callback(message: str, progress_pct: int, detail: str = ""):
                """Sync callback that puts updates in async queue - accepts 3 parameters"""
                try:
                    loop.call_soon_threadsafe(
                        progress_queue.put_nowait,
                        {'message': message, 'percent': progress_pct, 'detail': detail}
                    )
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
            
            # Run backtest in executor
            with concurrent.futures.ThreadPoolExecutor() as executor:
                backtest_future = loop.run_in_executor(
                    executor,
                    backtester.run,
                    screener_model,
                    {},  # screener_params
                    day_model,
                    {},  # day_model_params
                    start_date,
                    end_date,
                    universe,
                    top_n_stocks,
                    min_score,
                    force_execution,
                    sync_progress_callback
                )
                
                # Stream progress updates while backtest runs
                while not backtest_future.done():
                    try:
                        update = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                        yield f"data: {json.dumps({'type': 'progress', 'percent': update['percent'], 'message': update['message'], 'detail': update.get('detail', '')})}\n\n"
                    except asyncio.TimeoutError:
                        # No update in last second, continue waiting
                        continue
                
                # Get final results
                results = await backtest_future
            
            # Drain remaining progress updates
            while not progress_queue.empty():
                update = await progress_queue.get()
                yield f"data: {json.dumps({'type': 'progress', 'percent': update['percent'], 'message': update['message'], 'detail': update.get('detail', '')})}\n\n"
            
            # Format trades for JSON
            trades_list = []
            if 'trades' in results:
                for trade in results['trades'][:100]:  # Limit to 100 trades
                    trades_list.append({
                        'symbol': trade['symbol'],
                        'action': trade['action'],
                        'shares': trade['shares'],
                        'price': trade['price'],
                        'timestamp': trade['timestamp'].isoformat() if hasattr(trade['timestamp'], 'isoformat') else str(trade['timestamp']),
                        'reason': trade['reason'],
                        'pnl': trade['pnl'],
                        'pnl_pct': trade['pnl_pct'] * 100
                    })
            
            # Prepare final results
            final_results = {
                'status': 'success',
                'strategy': results['strategy'],
                'initial_capital': results['initial_capital'],
                'final_value': results['final_value'],
                'total_return_pct': results['total_return_pct'],
                'total_trades': results['total_trades'],
                'winning_trades': results['winning_trades'],
                'losing_trades': results['losing_trades'],
                'win_rate': results['win_rate'] * 100,
                'avg_win': results['avg_win'],
                'avg_loss': results['avg_loss'],
                'profit_factor': results['profit_factor'],
                'trades': trades_list,
                'unique_stocks_traded': results['unique_stocks_traded'],
                'screening_sessions': results['screening_sessions']
            }
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'percent': 100, 'message': 'Backtest complete!', 'results': final_results})}\n\n"
            
            logger.info(f"✅ SSE Backtest complete: {results['total_return_pct']:.2f}% return")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ SSE Backtest failed: {error_msg}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )


# ============================================================================
# LEGACY POST ENDPOINT (Kept for backward compatibility)
# ============================================================================

@router.post("/comprehensive-backtest")
async def run_comprehensive_backtest(params: ComprehensiveBacktestParams):
    """
    Run comprehensive backtest with daily screening + intraday trading
    (Legacy endpoint - returns results all at once)
    """
    try:
        logger.info(f"🚀 Starting comprehensive backtest: {params.screener_model} + {params.day_model}")
        
        # Create backtester using the imported class (works with either name)
        backtester = Backtester(
            api_key=settings.alpaca_key,
            api_secret=settings.alpaca_secret,
            initial_capital=params.initial_capital
        )
        
        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=params.days)
        
        # Handle manual selection
        if params.screener_model == 'manual':
            if not params.stock_universe:
                raise HTTPException(400, "Manual selection requires stock_universe parameter")
            universe = params.stock_universe
        else:
            universe = params.stock_universe if params.stock_universe else get_full_universe()
        
        logger.info(f"📊 Backtest params: {params.days} days, {len(universe)} stocks, top {params.top_n_stocks}")
        
        # Progress callback that logs to console
        def log_progress(message: str, progress_pct: int, detail: str = ""):
            """Log progress updates - accepts 3 parameters"""
            if detail:
                logger.info(f"[{progress_pct}%] {message} - {detail}")
            else:
                logger.info(f"[{progress_pct}%] {message}")
        
        # Run backtest with progress logging
        results = backtester.run(
            screener_model=params.screener_model,
            screener_params=params.screener_params,
            day_model=params.day_model,
            day_model_params=params.day_model_params,
            start_date=start_date,
            end_date=end_date,
            stock_universe=universe,
            top_n=params.top_n_stocks,
            min_score=params.min_score,
            force_execution=params.force_execution,
            progress_callback=log_progress
        )
        
        # Format trades for JSON
        trades_list = []
        if 'trades' in results:
            for trade in results['trades']:
                trades_list.append({
                    'symbol': trade['symbol'],
                    'action': trade['action'],
                    'shares': trade['shares'],
                    'price': trade['price'],
                    'timestamp': trade['timestamp'].isoformat() if hasattr(trade['timestamp'], 'isoformat') else str(trade['timestamp']),
                    'reason': trade['reason'],
                    'pnl': trade['pnl'],
                    'pnl_pct': trade['pnl_pct'] * 100
                })
        
        logger.info(f"✅ Backtest complete: {results['total_return_pct']:.2f}% return, {results['total_trades']} trades")
        
        return {
            'status': 'success',
            'strategy': results['strategy'],
            'initial_capital': results['initial_capital'],
            'final_value': results['final_value'],
            'total_return_pct': results['total_return_pct'],
            'total_trades': results['total_trades'],
            'winning_trades': results['winning_trades'],
            'losing_trades': results['losing_trades'],
            'win_rate': results['win_rate'] * 100,
            'avg_win': results['avg_win'],
            'avg_loss': results['avg_loss'],
            'profit_factor': results['profit_factor'],
            'trades': trades_list[:100],  # Limit to first 100 trades
            'unique_stocks_traded': results['unique_stocks_traded'],
            'screening_sessions': results['screening_sessions']
        }
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Backtest failed: {str(e)}")