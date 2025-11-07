"""
Backtest API Endpoints Module
Separate module for comprehensive backtesting endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings
from integrated_backtester import IntegratedBacktester
from stock_universe import get_full_universe

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


@router.post("/comprehensive-backtest")
async def run_comprehensive_backtest(params: ComprehensiveBacktestParams):
    """
    Run comprehensive backtest with daily screening + intraday trading
    Includes progress logging for monitoring
    """
    try:
        logger.info(f"🚀 Starting comprehensive backtest: {params.screener_model} + {params.day_model}")
        
        # Create backtester with proper authentication
        backtester = IntegratedBacktester(
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
        def log_progress(message: str, progress_pct: int):
            """Log progress updates"""
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
            progress_callback=log_progress  # ✅ Progress tracking
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