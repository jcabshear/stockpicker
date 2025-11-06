"""
Modular Autonomous Trading Bot with Auto Stock Selection
Clean main.py with separated dashboard templates
"""

import os
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Import dashboard templates
from dashboard import MAIN_DASHBOARD_HTML, SETTINGS_PAGE_HTML, BACKTEST_PAGE_HTML

# Import configurations
import sys
sys.path.insert(0, '/home/claude')

from config import settings

# Dynamic imports
try:
    from daily_selector import DailyStockSelector
    AUTO_SELECT_AVAILABLE = True
except ImportError:
    AUTO_SELECT_AVAILABLE = False
    print("⚠️ Auto-selection not available - using manual symbols")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL STATE
# ============================================================================

trader: Optional[object] = None
trading_task: Optional[asyncio.Task] = None
heartbeat_task: Optional[asyncio.Task] = None
selector_task: Optional[asyncio.Task] = None
stock_selector: Optional[DailyStockSelector] = None

# Runtime settings
runtime_settings = {
    "allow_trading": settings.allow_trading,
    "max_usd_per_order": settings.max_usd_per_order,
    "max_daily_loss": settings.max_daily_loss,
    "symbols": settings.symbols,
    "short_window": settings.short_window,
    "long_window": settings.long_window,
    "volume_threshold": settings.volume_threshold,
    "stop_loss_pct": settings.stop_loss_pct,
    "auto_select_stocks": settings.auto_select_stocks if AUTO_SELECT_AVAILABLE else False,
    "min_stock_score": settings.min_stock_score,
}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SettingsUpdate(BaseModel):
    allow_trading: bool
    max_usd_per_order: float
    max_daily_loss: float
    symbols: str
    short_window: int
    long_window: int
    volume_threshold: float
    stop_loss_pct: float
    auto_select_stocks: bool
    min_stock_score: float

class TradingToggle(BaseModel):
    enabled: bool

class BacktestParams(BaseModel):
    short_window: int
    long_window: int
    volume_threshold: float
    stop_loss_pct: float
    symbols: str
    days: int
    initial_capital: float
    # Screener settings
    use_screener: bool = False
    min_stock_score: float = 60
    top_n_stocks: int = 3
    screen_frequency: str = "daily"  # 'daily' or 'weekly'

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Trading Bot API")


@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    await initialize_bot()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global trading_task, heartbeat_task, selector_task
    
    print("\n🛑 Shutting down...")
    if trading_task:
        trading_task.cancel()
    if heartbeat_task:
        heartbeat_task.cancel()
    if selector_task:
        selector_task.cancel()
    print("✅ Shutdown complete")


async def update_trading_symbols(new_symbols: list):
    """Callback when stock selector picks new symbols"""
    global runtime_settings
    
    print(f"\n📊 Updating trading symbols: {', '.join(new_symbols)}")
    runtime_settings["symbols"] = ','.join(new_symbols)
    await initialize_bot()


async def initialize_bot():
    """Initialize or reinitialize the bot"""
    global trader, trading_task, heartbeat_task, selector_task, stock_selector
    
    # Cancel existing tasks
    if trading_task:
        trading_task.cancel()
        try:
            await trading_task
        except asyncio.CancelledError:
            pass
    
    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
    
    print("\n" + "="*80)
    print("🚀 INITIALIZING TRADING BOT")
    print("="*80)
    logger.info("Starting bot initialization...")
    
    # Handle stock selection
    if runtime_settings.get("auto_select_stocks", False) and AUTO_SELECT_AVAILABLE:
        print("\n🎯 AUTO STOCK SELECTION ENABLED")
        
        if stock_selector is None:
            stock_selector = DailyStockSelector(settings.alpaca_key, settings.alpaca_secret)
        
        symbols = stock_selector.get_current_symbols()
        runtime_settings["symbols"] = ','.join(symbols)
        
        print(f"   Selected stocks: {', '.join(symbols)}")
        print(f"   Min score threshold: {runtime_settings.get('min_stock_score', 60)}")
        
        if selector_task is None or selector_task.done():
            selector_task = asyncio.create_task(
                stock_selector.auto_select_loop(update_trading_symbols)
            )
    else:
        print("\n📋 Using manually configured symbols")
        symbols = runtime_settings["symbols"]
    
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(',')]
    
    port = int(os.getenv('PORT', 10000))
    
    print(f"\n📋 Configuration:")
    print(f"   Mode: {'PAPER' if settings.paper else 'LIVE'}")
    print(f"   Trading: {'ENABLED' if runtime_settings['allow_trading'] else 'DISABLED'}")
    print(f"   Auto-Select: {'ENABLED' if runtime_settings.get('auto_select_stocks') else 'DISABLED'}")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Max Position: ${runtime_settings['max_usd_per_order']}")
    print(f"   Max Daily Loss: ${runtime_settings['max_daily_loss']}")
    print(f"   Strategy: SMA ({runtime_settings['short_window']}/{runtime_settings['long_window']})")
    print(f"   Dashboard: http://0.0.0.0:{port}")
    print("="*80 + "\n")
    
    try:
        from sma_crossover_strategy import SMACrossoverStrategy
        from live_trader import LiveTrader
        
        strategy = SMACrossoverStrategy(
            short_window=runtime_settings["short_window"],
            long_window=runtime_settings["long_window"],
            volume_threshold=runtime_settings["volume_threshold"],
            stop_loss_pct=runtime_settings["stop_loss_pct"]
        )
        
        trader = LiveTrader(strategy)
        trader.allow_trading = runtime_settings["allow_trading"]
        trader.max_position_size = runtime_settings["max_usd_per_order"]
        trader.max_daily_loss = runtime_settings["max_daily_loss"]
        
        print("✅ Bot initialized successfully\n")
        logger.info("Bot initialized successfully")
        
        trading_task = asyncio.create_task(trader.run(symbols))
        heartbeat_task = asyncio.create_task(heartbeat())
        
        logger.info("All background tasks running")
    except ImportError as e:
        print(f"⚠️ Could not import trading modules: {e}")
        print("   Bot running in monitor-only mode")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve main dashboard"""
    return MAIN_DASHBOARD_HTML


@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    """Serve settings page"""
    return SETTINGS_PAGE_HTML


@app.get("/backtest", response_class=HTMLResponse)
async def backtest_page():
    """Serve backtest page"""
    return BACKTEST_PAGE_HTML


@app.post("/api/backtest")
async def run_backtest(params: BacktestParams):
    """Run a backtest with given parameters"""
    try:
        from datetime import datetime, timedelta
        from sma_crossover_strategy import SMACrossoverStrategy
        
        logger.info(f"Starting backtest: {params.symbols} for {params.days} days (screener: {params.use_screener})")
        
        # Create strategy with test parameters
        strategy = SMACrossoverStrategy(
            short_window=params.short_window,
            long_window=params.long_window,
            volume_threshold=params.volume_threshold,
            stop_loss_pct=params.stop_loss_pct
        )
        
        # Parse symbols
        symbols = [s.strip() for s in params.symbols.split(',')]
        
        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=params.days)
        
        if params.use_screener:
            # Use integrated backtester with screening
            from integrated_backtester import IntegratedBacktester
            
            backtester = IntegratedBacktester(
                api_key=settings.alpaca_key,
                api_secret=settings.alpaca_secret,
                initial_capital=params.initial_capital
            )
            
            # Run with screening
            results = backtester.run(
                strategy=strategy,
                stock_universe=symbols,  # These become the screening universe
                start_date=start_date,
                end_date=end_date,
                min_score=params.min_stock_score,
                top_n=params.top_n_stocks,
                screen_frequency=params.screen_frequency
            )
        else:
            # Use regular backtester with fixed symbols
            from backtester import Backtester
            
            backtester = Backtester(
                api_key=settings.alpaca_key,
                api_secret=settings.alpaca_secret,
                initial_capital=params.initial_capital
            )
            
            # Run normal backtest
            results = backtester.run(
                strategy=strategy,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date
            )
        
        # Convert trades DataFrame to list of dicts for JSON
        trades_list = []
        if 'trades' in results and not results['trades'].empty:
            trades_list = results['trades'].to_dict('records')
            # Convert timestamps to ISO format
            for trade in trades_list:
                if 'timestamp' in trade:
                    trade['timestamp'] = trade['timestamp'].isoformat()
        
        # Return results
        response = {
            "strategy": results['strategy'],
            "initial_capital": results['initial_capital'],
            "final_value": results['final_value'],
            "total_return": results['total_return'],
            "total_return_pct": results['total_return_pct'],
            "total_trades": results['total_trades'],
            "winning_trades": results['winning_trades'],
            "losing_trades": results['losing_trades'],
            "win_rate": results['win_rate'],
            "avg_win": results['avg_win'],
            "avg_loss": results['avg_loss'],
            "profit_factor": results['profit_factor'],
            "sharpe_ratio": results['sharpe_ratio'],
            "max_drawdown": results['max_drawdown'],
            "max_drawdown_pct": results['max_drawdown_pct'],
            "trades": trades_list
        }
        
        # Add screening-specific metrics if available
        if 'unique_stocks_traded' in results:
            response['unique_stocks_traded'] = results['unique_stocks_traded']
            response['screening_sessions'] = results['screening_sessions']
        
        return response
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Backtest failed: {str(e)}")


@app.get("/health")
def health():
    """Health check endpoint"""
    if not trader:
        return {"status": "initializing", "message": "Bot is starting up..."}
    
    return {
        "status": "running",
        "strategy": trader.strategy.name,
        "trading_enabled": trader.allow_trading,
        "auto_select": runtime_settings.get("auto_select_stocks", False),
        "daily_pnl": trader.daily_pnl,
        "positions": len(trader.positions),
        "total_trades": trader.total_trades,
        "market_open": trader.is_market_open()
    }


@app.get("/account")
def get_account():
    """Get Alpaca account information"""
    try:
        from alpaca.trading.client import TradingClient
        
        client = TradingClient(settings.alpaca_key, settings.alpaca_secret, paper=settings.paper)
        account = client.get_account()
        
        return {
            "equity": float(account.equity),
            "buying_power": float(account.buying_power),
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "today_pnl": float(account.equity) - float(account.last_equity),
            "status": account.status
        }
    except Exception as e:
        logger.error(f"Error fetching account data: {e}")
        return {
            "equity": 0,
            "buying_power": 0,
            "cash": 0,
            "portfolio_value": 0,
            "today_pnl": 0,
            "status": "error"
        }


@app.get("/positions")
def get_positions():
    """Get current positions"""
    if not trader:
        return {"positions": [], "message": "Bot initializing..."}
    
    return {
        "positions": [
            {
                "symbol": p.symbol,
                "shares": p.shares,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "pnl": p.pnl,
                "pnl_pct": p.pnl_pct * 100,
                "entry_time": p.entry_time.isoformat()
            }
            for p in trader.positions.values()
        ]
    }


@app.get("/stats")
def get_stats():
    """Get trading stats"""
    if not trader:
        return {"message": "Bot initializing..."}
    
    win_rate = (trader.winning_trades / trader.total_trades * 100) if trader.total_trades > 0 else 0
    
    return {
        "strategy": trader.strategy.name,
        "total_trades": trader.total_trades,
        "winning_trades": trader.winning_trades,
        "losing_trades": trader.losing_trades,
        "win_rate": round(win_rate, 2),
        "daily_pnl": round(trader.daily_pnl, 2),
        "max_position_size": trader.max_position_size,
        "max_daily_loss": trader.max_daily_loss
    }


@app.get("/api/settings")
def get_settings_api():
    """Get current settings as JSON"""
    return runtime_settings


@app.post("/toggle-trading")
async def toggle_trading(toggle: TradingToggle):
    """Toggle trading on/off"""
    global runtime_settings, trader
    
    runtime_settings["allow_trading"] = toggle.enabled
    
    if trader:
        trader.allow_trading = toggle.enabled
        
    status = "enabled" if toggle.enabled else "disabled"
    logger.info(f"Trading {status} via dashboard toggle")
    print(f"\n{'🟢' if toggle.enabled else '🔴'} Trading {status} via dashboard")
    
    return {
        "ok": True,
        "trading_enabled": toggle.enabled,
        "message": f"Trading {status}"
    }


@app.post("/settings")
async def update_settings(new_settings: SettingsUpdate):
    """Update settings and restart bot"""
    global runtime_settings
    
    # Validate
    if new_settings.short_window >= new_settings.long_window:
        raise HTTPException(400, "Short window must be less than long window")
    
    if new_settings.max_usd_per_order < 10:
        raise HTTPException(400, "Max USD per order must be at least $10")
    
    if new_settings.stop_loss_pct < 0.01 or new_settings.stop_loss_pct > 0.5:
        raise HTTPException(400, "Stop loss must be between 1% and 50%")
    
    # Update runtime settings
    runtime_settings.update(new_settings.dict())
    
    logger.info("Settings updated, restarting bot...")
    print("\n⚙️ Settings updated, restarting bot with new configuration...")
    
    # Reinitialize bot with new settings
    await initialize_bot()
    
    return {"ok": True, "message": "Settings updated and bot restarted"}


@app.post("/kill")
def kill(token: str):
    """Emergency stop"""
    kill_token = os.getenv('KILL_TOKEN', 'let-me-in')
    
    if token != kill_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if trader:
        trader.allow_trading = False
        runtime_settings["allow_trading"] = False
        logger.warning("EMERGENCY STOP: Trading disabled via API")
        print("🚨 EMERGENCY STOP: Trading disabled via API")
    
    return {"ok": True, "message": "Trading disabled"}


@app.get("/screen")
async def manual_screen():
    """Manually trigger stock screening"""
    if not AUTO_SELECT_AVAILABLE:
        raise HTTPException(503, "Auto-selection not available")
    
    if stock_selector is None:
        raise HTTPException(503, "Stock selector not initialized")
    
    symbols = stock_selector.select_daily_stocks()
    
    return {
        "ok": True,
        "symbols": symbols,
        "message": f"Selected {len(symbols)} stocks. Update settings to use them."
    }


# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def heartbeat():
    """Periodic heartbeat"""
    logger.info("Heartbeat task started")
    await asyncio.sleep(5)
    
    while True:
        try:
            if trader:
                win_rate = (trader.winning_trades / trader.total_trades * 100) if trader.total_trades > 0 else 0
                market_status = "🟢 OPEN" if trader.is_market_open() else "🔴 CLOSED"
                auto_status = "🎯 AUTO" if runtime_settings.get("auto_select_stocks") else "📋 MANUAL"
                message = (
                    f"💓 Bot alive | "
                    f"Market: {market_status} | "
                    f"Mode: {auto_status} | "
                    f"Positions: {len(trader.positions)} | "
                    f"Trades: {trader.total_trades} | "
                    f"Win Rate: {win_rate:.1f}% | "
                    f"Daily P&L: ${trader.daily_pnl:.2f}"
                )
                logger.info(message)
        except Exception as e:
            logger.error(f"Error in heartbeat: {e}")
        
        await asyncio.sleep(60)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv('PORT', 10000))
    
    print("=" * 80)
    print("STARTING TRADING BOT WITH AUTO STOCK SELECTION")
    print("=" * 80)
    logger.info(f"Starting application on port {port}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise