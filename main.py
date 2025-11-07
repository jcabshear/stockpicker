"""
Enhanced Trading Bot Main Application
Complete version with SSE streaming and optimized backtesting

Features:
- Real-time SSE progress updates for backtests
- Optimized batch data fetching
- Enhanced position analysis
- Publish backtest to live trading
- Comprehensive monitoring
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import HTML templates
from enhanced_dashboard import ENHANCED_DASHBOARD_HTML
from enhanced_settings import ENHANCED_SETTINGS_HTML
from enhanced_backtest import ENHANCED_BACKTEST_HTML

# Import core modules
from config import settings
from settings_manager import settings_manager
from position_analyzer import PositionAnalyzer

# Import modular endpoints
from backtest_endpoints import router as backtest_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Enhanced Trading Bot API",
    description="Automated trading bot with real-time backtesting and monitoring",
    version="2.0.0"
)

# Add CORS middleware for SSE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include backtest endpoints with SSE streaming
app.include_router(backtest_router)

# ============================================================================
# GLOBAL STATE
# ============================================================================

trader: Optional[object] = None
position_analyzer: Optional[PositionAnalyzer] = None

# Initialize position analyzer with IEX feed (free tier)
try:
    position_analyzer = PositionAnalyzer(
        settings.alpaca_key,
        settings.alpaca_secret,
        feed="iex"
    )
    logger.info("✅ Position analyzer initialized")
except Exception as e:
    logger.error(f"Failed to initialize position analyzer: {e}")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RiskParamsUpdate(BaseModel):
    """Risk parameters update model"""
    max_usd_per_order: float
    max_daily_loss: float


class BacktestPublishConfig(BaseModel):
    """Configuration to publish from backtest to live"""
    screener_model: str
    screener_params: dict
    day_model: str
    day_model_params: dict
    top_n_stocks: int
    min_score: float
    force_execution: bool


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
    """Serve enhanced backtest page with real-time SSE progress"""
    return ENHANCED_BACKTEST_HTML


# ============================================================================
# API ENDPOINTS - SYSTEM STATUS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed system status"""
    try:
        from alpaca.trading.client import TradingClient
        
        trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        
        account = trading_client.get_account()
        clock = trading_client.get_clock()
        positions = trading_client.get_all_positions()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "trading_enabled": settings.allow_trading,
            "paper_mode": settings.paper,
            "market_open": clock.is_open,
            "next_open": clock.next_open.isoformat(),
            "next_close": clock.next_close.isoformat(),
            "account": {
                "status": account.status,
                "cash": float(account.cash),
                "equity": float(account.equity),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value)
            },
            "positions": {
                "count": len(positions),
                "total_value": sum(float(p.market_value) for p in positions)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(500, f"Health check failed: {str(e)}")


@app.get("/api/info")
async def api_info():
    """Get API and bot information"""
    return {
        "name": "Enhanced Trading Bot",
        "version": "2.0.0",
        "features": [
            "Real-time SSE backtest streaming",
            "Optimized batch data fetching",
            "Multiple screening models",
            "Intraday trading models",
            "Position analysis",
            "Live trading integration"
        ],
        "endpoints": {
            "dashboard": "/",
            "settings": "/settings",
            "backtest": "/backtest",
            "health": "/health",
            "positions": "/positions",
            "stats": "/stats"
        }
    }


# ============================================================================
# API ENDPOINTS - POSITIONS & TRADING
# ============================================================================

@app.get("/positions")
async def get_positions():
    """Get current positions with P&L"""
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
                'qty': float(pos.qty),
                'avg_entry_price': float(pos.avg_entry_price),
                'current_price': float(pos.current_price),
                'market_value': float(pos.market_value),
                'cost_basis': float(pos.cost_basis),
                'unrealized_pl': float(pos.unrealized_pl),
                'unrealized_plpc': float(pos.unrealized_plpc) * 100,
                'side': pos.side
            })
        
        return {
            'status': 'success',
            'count': len(positions_data),
            'positions': positions_data
        }
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(500, f"Failed to get positions: {str(e)}")


@app.get("/api/position-details/{symbol}")
async def get_position_details(symbol: str):
    """
    Get detailed analysis for a specific position
    Includes entry logic, scenarios, and confidence scores
    """
    try:
        from alpaca.trading.client import TradingClient
        
        trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        
        # Get position
        try:
            position = trading_client.get_open_position(symbol)
        except:
            raise HTTPException(404, f"No open position for {symbol}")
        
        # Convert to dict for analyzer
        position_dict = {
            'symbol': position.symbol,
            'shares': float(position.qty),
            'entry_price': float(position.avg_entry_price),
            'current_price': float(position.current_price),
            'entry_time': None  # Not available from Alpaca position object
        }
        
        # Get current settings for model info
        current_config = settings_manager.get_active_config()
        
        # Analyze position
        if position_analyzer:
            analysis = position_analyzer.analyze_position(
                position_dict,
                screening_model=current_config['screening']['model'],
                daytrade_model=current_config['daytrade']['model']
            )
            
            return {
                'status': 'success',
                'analysis': analysis
            }
        else:
            return {
                'status': 'error',
                'message': 'Position analyzer not initialized'
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze position {symbol}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to analyze position: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get trading statistics"""
    try:
        from alpaca.trading.client import TradingClient
        
        trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        
        account = trading_client.get_account()
        positions = trading_client.get_all_positions()
        
        # Calculate total P&L
        total_pl = sum(float(p.unrealized_pl) for p in positions)
        total_pl_pct = (total_pl / float(account.portfolio_value)) * 100 if float(account.portfolio_value) > 0 else 0
        
        return {
            'status': 'success',
            'account_value': float(account.portfolio_value),
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'positions_count': len(positions),
            'total_unrealized_pl': total_pl,
            'total_unrealized_pl_pct': total_pl_pct,
            'winning_positions': sum(1 for p in positions if float(p.unrealized_pl) > 0),
            'losing_positions': sum(1 for p in positions if float(p.unrealized_pl) < 0),
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(500, f"Failed to get stats: {str(e)}")


# ============================================================================
# API ENDPOINTS - SETTINGS MANAGEMENT
# ============================================================================

@app.get("/api/settings")
async def get_settings():
    """Get current live trading settings"""
    try:
        config = settings_manager.get_active_config()
        return {
            'status': 'success',
            'settings': config
        }
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(500, f"Failed to get settings: {str(e)}")


@app.post("/api/publish-backtest")
async def publish_backtest(config: BacktestPublishConfig):
    """Publish backtest configuration to live trading"""
    try:
        config_dict = {
            'screener_model': config.screener_model,
            'screener_params': config.screener_params,
            'day_model': config.day_model,
            'day_model_params': config.day_model_params,
            'top_n_stocks': config.top_n_stocks,
            'min_score': config.min_score,
            'force_execution': config.force_execution
        }
        
        result = settings_manager.publish_backtest_settings(config_dict)
        
        logger.info(f"✅ Published backtest config to live trading: {config.screener_model} + {config.day_model}")
        
        return {
            'status': 'success',
            'message': 'Configuration published to live trading',
            'new_settings': result
        }
    except Exception as e:
        logger.error(f"Failed to publish settings: {e}")
        raise HTTPException(500, f"Failed to publish settings: {str(e)}")


@app.post("/api/update-risk-params")
async def update_risk_params(params: RiskParamsUpdate):
    """Update risk management parameters"""
    try:
        settings_manager.update_risk_params({
            'max_usd_per_order': params.max_usd_per_order,
            'max_daily_loss': params.max_daily_loss
        })
        
        logger.info(f"✅ Updated risk params: max_order=${params.max_usd_per_order}, max_loss=${params.max_daily_loss}")
        
        return {
            'status': 'success',
            'message': 'Risk parameters updated',
            'new_params': {
                'max_usd_per_order': params.max_usd_per_order,
                'max_daily_loss': params.max_daily_loss
            }
        }
    except Exception as e:
        logger.error(f"Failed to update risk params: {e}")
        raise HTTPException(500, f"Failed to update risk params: {str(e)}")


# ============================================================================
# API ENDPOINTS - EMERGENCY CONTROLS
# ============================================================================

@app.post("/kill")
async def emergency_stop(token: str):
    """
    Emergency stop - disables all trading immediately
    Requires token for safety
    """
    if token != "let-me-in":
        raise HTTPException(403, "Invalid token")
    
    try:
        # Set trading disabled globally
        settings.allow_trading = False
        
        # Close all positions if needed
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import ClosePositionRequest
        
        trading_client = TradingClient(
            settings.alpaca_key,
            settings.alpaca_secret,
            paper=settings.paper
        )
        
        positions = trading_client.get_all_positions()
        
        logger.warning(f"🚨 EMERGENCY STOP TRIGGERED - Disabling trading, {len(positions)} positions open")
        
        return {
            'status': 'success',
            'message': 'Trading disabled',
            'trading_enabled': False,
            'open_positions': len(positions),
            'note': 'Trading is now disabled. Positions remain open. Close manually if needed.'
        }
    except Exception as e:
        logger.error(f"Emergency stop failed: {e}")
        raise HTTPException(500, f"Emergency stop failed: {str(e)}")


# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("="*80)
    logger.info("🚀 Starting Enhanced Trading Bot API v2.0")
    logger.info("="*80)
    logger.info(f"Alpaca Paper Mode: {settings.paper}")
    logger.info(f"Trading Enabled: {settings.allow_trading}")
    logger.info(f"Data Feed: {settings.feed}")
    
    if not settings.alpaca_key or not settings.alpaca_secret:
        logger.error("❌ Missing Alpaca credentials!")
        logger.error("   Set ALPACA_KEY and ALPACA_SECRET environment variables")
        return
    
    logger.info("✅ Bot API initialized successfully")
    logger.info("="*80)
    logger.info("📊 Dashboard: http://localhost:10000")
    logger.info("⚙️  Settings: http://localhost:10000/settings")
    logger.info("🧪 Backtest: http://localhost:10000/backtest")
    logger.info("💚 Health: http://localhost:10000/health")
    logger.info("="*80)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down Enhanced Trading Bot API")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Check for required environment variables
    if not settings.alpaca_key or not settings.alpaca_secret:
        logger.error("❌ ALPACA_KEY and ALPACA_SECRET must be set!")
        logger.error("   Set them as environment variables or in .env file")
        exit(1)
    
    # Run server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10000,
        reload=False,
        log_level="info"
    )