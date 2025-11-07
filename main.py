"""
Enhanced Trading Bot Main Application
Complete version with all endpoints and modular structure

Features:
- Fixed authentication for backtesting
- Manual screening model
- Enhanced position details with live charts
- Publish backtest to live functionality
- Progress tracking for backtests
- Modular endpoint structure
"""

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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

app = FastAPI(title="Enhanced Trading Bot API")

# Include backtest endpoints from separate module
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
# API ENDPOINTS - SYSTEM STATUS
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


# ============================================================================
# API ENDPOINTS - POSITIONS
# ============================================================================

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


# ============================================================================
# API ENDPOINTS - SETTINGS
# ============================================================================

@app.get("/api/settings")
async def get_settings():
    """Get current trading settings"""
    try:
        active_config = settings_manager.get_active_config()
        return {
            'status': 'success',
            'settings': active_config
        }
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(500, f"Failed to get settings: {str(e)}")


@app.post("/api/publish-backtest")
async def publish_backtest(config: dict):
    """Publish backtest configuration to live trading"""
    try:
        result = settings_manager.publish_backtest_settings(config)
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
# STARTUP & SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting Enhanced Trading Bot API")
    logger.info(f"Alpaca Paper Mode: {settings.paper}")
    logger.info(f"Trading Enabled: {settings.allow_trading}")
    
    if not settings.alpaca_key or not settings.alpaca_secret:
        logger.error("❌ Missing Alpaca credentials!")
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