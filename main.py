"""
Enhanced Trading Bot Main Application
Includes:
- Fixed authentication for backtesting
- Manual screening model
- Enhanced position details with live charts and analysis
- Publish backtest to live functionality
- Updated settings page showing active models
"""

import os
import asyncio
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Import enhanced dashboard templates
from enhanced_dashboard import ENHANCED_DASHBOARD_HTML
from enhanced_settings import ENHANCED_SETTINGS_HTML
from enhanced_backtest import ENHANCED_BACKTEST_HTML

# Import core modules
from config import settings
from settings_manager import settings_manager
from position_analyzer import PositionAnalyzer, get_live_price_data
from manual_screener import ManualScreener

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Enhanced Trading Bot API")

# ============================================================================
# GLOBAL STATE
# ============================================================================

trader: Optional[object] = None
position_analyzer: Optional[PositionAnalyzer] = None

# Initialize position analyzer with IEX feed (free tier)
try:
    position_analyzer = PositionAnalyzer(settings.alpaca_key, settings.alpaca_secret, feed="iex")
except Exception as e:
    logger.error(f"Failed to initialize position analyzer: {e}")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ComprehensiveBacktestParams(BaseModel):
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

class RiskParamsUpdate(BaseModel):
    max_usd_per_order: float
    max_daily_loss: float

# ============================================================================
# HTML PAGE ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve enhanced dashboard with position details"""
    return ENHANCED_DASHBOARD_HTML

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    """Serve enhanced settings page showing active models"""
    return ENHANCED_SETTINGS_HTML

@app.get("/backtest", response_class=HTMLResponse)
async def backtest_page():
    """Serve enhanced backtest page with publish to live"""
    return ENHANCED_BACKTEST_HTML

# ============================================================================
# API ENDPOINTS - EXISTING
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from alpaca.trading.client import TradingClient
        
        trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        
        account = trading_client.get_account()
        clock = trading_client.get_clock()
        
        return {
            "status": "healthy",
            "trading_enabled": settings.allow_trading,
            "market_open": clock.is_open,
            "account_status": account.status,
            "cash": float(account.cash),
            "equity": float(account.equity),
            "positions": len(trading_client.get_all_positions())
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(500, f"Health check failed: {str(e)}")

@app.get("/positions")
async def get_positions():
    """Get current positions"""
    try:
        from alpaca.trading.client import TradingClient
        
        trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        
        positions = trading_client.get_all_positions()
        
        positions_data = []
        for pos in positions:
            positions_data.append({
                'symbol': pos.symbol,
                'shares': float(pos.qty),
                'entry_price': float(pos.avg_entry_price),
                'current_price': float(pos.current_price),
                'pnl': float(pos.unrealized_pl),
                'pnl_pct': float(pos.unrealized_plpc) * 100,
                'market_value': float(pos.market_value)
            })
        
        return {'positions': positions_data}
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(500, f"Failed to get positions: {str(e)}")

# ============================================================================
# API ENDPOINTS - NEW ENHANCEMENTS
# ============================================================================

@app.get("/api/position-details/{symbol}")
async def get_position_details(symbol: str):
    """Get comprehensive details for a specific position"""
    try:
        if not position_analyzer:
            raise HTTPException(500, "Position analyzer not initialized")
        
        # Get current position from Alpaca
        from alpaca.trading.client import TradingClient
        
        trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        
        positions = trading_client.get_all_positions()
        position_data = None
        
        for pos in positions:
            if pos.symbol == symbol:
                position_data = {
                    'symbol': pos.symbol,
                    'shares': float(pos.qty),
                    'entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'entry_time': None  # Not available from Alpaca
                }
                break
        
        if not position_data:
            raise HTTPException(404, f"Position not found for {symbol}")
        
        # Get active models
        active_config = settings_manager.get_active_config()
        screening_model = active_config['screening']['model']
        daytrade_model = active_config['daytrade']['model']
        
        # Analyze position
        analysis = position_analyzer.analyze_position(
            position_data,
            screening_model=screening_model,
            daytrade_model=daytrade_model
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze position {symbol}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to analyze position: {str(e)}")

@app.get("/api/live-chart/{symbol}")
async def get_live_chart(symbol: str):
    """Get live chart data for a symbol"""
    try:
        chart_data = get_live_price_data(symbol, settings.alpaca_key, settings.alpaca_secret)
        return chart_data
    except Exception as e:
        logger.error(f"Failed to get chart data for {symbol}: {e}")
        raise HTTPException(500, f"Failed to get chart data: {str(e)}")

@app.get("/api/active-config")
async def get_active_config():
    """Get currently active trading configuration"""
    try:
        config = settings_manager.get_active_config()
        return config
    except Exception as e:
        logger.error(f"Failed to get active config: {e}")
        raise HTTPException(500, f"Failed to get config: {str(e)}")

@app.post("/api/publish-to-live")
async def publish_to_live(params: ComprehensiveBacktestParams):
    """Publish backtest configuration to live trading"""
    try:
        # Convert params to dict
        config = {
            'screener_model': params.screener_model,
            'screener_params': params.screener_params,
            'day_model': params.day_model,
            'day_model_params': params.day_model_params,
            'top_n_stocks': params.top_n_stocks,
            'min_score': params.min_score,
            'force_execution': params.force_execution,
            'days': params.days,
            'initial_capital': params.initial_capital
        }
        
        # Publish to settings manager
        result = settings_manager.publish_backtest_settings(config)
        
        logger.info(f"Published settings to live: {params.screener_model} + {params.day_model}")
        
        return result
    except Exception as e:
        logger.error(f"Failed to publish to live: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to publish: {str(e)}")

@app.post("/api/update-risk-params")
async def update_risk_params(params: RiskParamsUpdate):
    """Update risk management parameters"""
    try:
        settings_manager.update_risk_params(
            max_usd_per_order=params.max_usd_per_order,
            max_daily_loss=params.max_daily_loss
        )
        
        return {'status': 'success', 'message': 'Risk parameters updated'}
    except Exception as e:
        logger.error(f"Failed to update risk params: {e}")
        raise HTTPException(500, f"Failed to update risk params: {str(e)}")

@app.post("/api/comprehensive-backtest")
async def run_comprehensive_backtest(params: ComprehensiveBacktestParams):
    """Run comprehensive backtest with daily screening + intraday trading"""
    try:
        from datetime import datetime, timedelta
        from integrated_backtester import IntegratedBacktester
        from stock_universe import get_full_universe
        from manual_screener import ManualScreener
        
        logger.info(f"Starting comprehensive backtest: {params.screener_model} + {params.day_model}")
        
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
            # Use full universe if not manual
            universe = params.stock_universe if params.stock_universe else get_full_universe()
        
        logger.info(f"Backtest params: {params.days} days, {len(universe)} stocks, top {params.top_n_stocks}")
        
        # Run backtest
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
            force_execution=params.force_execution
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
                    'pnl': trade.get('pnl', 0),
                    'pnl_pct': trade.get('pnl_pct', 0)
                })
        
        # Return results
        response = {
            'strategy': f"{params.screener_model} + {params.day_model}",
            'initial_capital': results['initial_capital'],
            'final_value': results['final_value'],
            'total_return': results['total_return'],
            'total_return_pct': results['total_return_pct'],
            'total_trades': results['total_trades'],
            'winning_trades': results['winning_trades'],
            'losing_trades': results['losing_trades'],
            'win_rate': results['win_rate'],
            'avg_win': results['avg_win'],
            'avg_loss': results['avg_loss'],
            'profit_factor': results['profit_factor'],
            'sharpe_ratio': results['sharpe_ratio'],
            'max_drawdown': results['max_drawdown'],
            'max_drawdown_pct': results['max_drawdown_pct'],
            'trades': trades_list
        }
        
        # Add screening-specific metrics
        if 'unique_stocks_traded' in results:
            response['unique_stocks_traded'] = results['unique_stocks_traded']
        if 'screening_sessions' in results:
            response['screening_sessions'] = results['screening_sessions']
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Backtest failed: {str(e)}")

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    logger.info("Starting Enhanced Trading Bot API")
    logger.info(f"Alpaca Paper Mode: {settings.paper}")
    logger.info(f"Trading Enabled: {settings.allow_trading}")
    
    # Validate credentials
    if not settings.alpaca_key or not settings.alpaca_secret:
        logger.error("⚠️  ERROR: Alpaca credentials not found!")
        logger.error("   Set ALPACA_KEY and ALPACA_SECRET environment variables")
        return
    
    logger.info("✅ Bot API initialized successfully")
    logger.info("📊 Dashboard available at http://localhost:10000")
    logger.info("⚙️  Settings available at http://localhost:10000/settings")
    logger.info("🧪 Backtesting available at http://localhost:10000/backtest")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10000,
        reload=False
    )