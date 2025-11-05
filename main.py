"""
Modular Autonomous Trading Bot
Uses separate strategy and trader components
"""

import os
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
import uvicorn

from sma_crossover_strategy import SMACrossoverStrategy
from live_trader import LiveTrader
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL STATE
# ============================================================================

trader: Optional[LiveTrader] = None
trading_task: Optional[asyncio.Task] = None
heartbeat_task: Optional[asyncio.Task] = None


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Trading Bot API")


@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    global trader, trading_task, heartbeat_task
    
    print("\n" + "="*80)
    print("🚀 INITIALIZING TRADING BOT")
    print("="*80)
    logger.info("Starting bot initialization...")
    
    # Parse symbols
    symbols = settings.symbols
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(',')]
    
    port = int(os.getenv('PORT', 10000))
    
    print(f"📋 Configuration:")
    print(f"   Mode: {'PAPER' if settings.paper else 'LIVE'}")
    print(f"   Trading: {'ENABLED' if settings.allow_trading else 'DISABLED'}")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Data Feed: {settings.feed.upper()}")
    print(f"   Max Position: ${settings.max_usd_per_order}")
    print(f"   Max Daily Loss: ${settings.max_daily_loss}")
    print(f"   Strategy: SMA Crossover ({settings.short_window}/{settings.long_window})")
    print(f"   API Port: {port}")
    print("="*80 + "\n")
    
    # Create strategy
    print("📊 Creating strategy...")
    strategy = SMACrossoverStrategy(
        short_window=settings.short_window,
        long_window=settings.long_window,
        volume_threshold=settings.volume_threshold,
        stop_loss_pct=settings.stop_loss_pct
    )
    print(f"✅ Strategy created: {strategy.name}")
    logger.info(f"Strategy created: {strategy.name}")
    
    # Create trader
    print("🤖 Creating trader...")
    trader = LiveTrader(strategy)
    print("✅ Trader created")
    logger.info("Trader initialized")
    
    print("\n✅ Bot initialized successfully")
    print(f"🌐 API available at http://0.0.0.0:{port}")
    print(f"📊 Health check: http://0.0.0.0:{port}/health\n")
    
    # Start background tasks
    print("🚀 Starting background tasks...")
    logger.info("Starting background tasks...")
    
    trading_task = asyncio.create_task(trader.run(symbols))
    heartbeat_task = asyncio.create_task(heartbeat())
    
    print("✅ Background tasks started\n")
    logger.info("All background tasks running")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global trading_task, heartbeat_task
    
    print("\n🛑 Shutting down...")
    logger.info("Initiating shutdown...")
    
    if trading_task:
        trading_task.cancel()
        logger.info("Trading task cancelled")
    
    if heartbeat_task:
        heartbeat_task.cancel()
        logger.info("Heartbeat task cancelled")
    
    print("✅ Shutdown complete")
    logger.info("Shutdown complete")


@app.get("/")
def root():
    """API root"""
    return {
        "app": "Trading Bot",
        "version": "2.0",
        "mode": "paper" if settings.paper else "live",
        "status": "running" if trader else "initializing",
        "endpoints": {
            "health": "/health",
            "positions": "/positions",
            "stats": "/stats",
            "kill": "POST /kill?token=<your-token>"
        }
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    if not trader:
        return {
            "status": "initializing",
            "message": "Bot is starting up..."
        }
    
    return {
        "status": "running",
        "strategy": trader.strategy.name,
        "trading_enabled": trader.allow_trading,
        "daily_pnl": trader.daily_pnl,
        "positions": len(trader.positions),
        "total_trades": trader.total_trades,
        "market_open": trader.is_market_open()
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


@app.post("/kill")
def kill(token: str):
    """Emergency stop"""
    kill_token = os.getenv('KILL_TOKEN', 'let-me-in')
    
    if token != kill_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if trader:
        trader.allow_trading = False
        logger.warning("EMERGENCY STOP: Trading disabled via API")
        print("🚨 EMERGENCY STOP: Trading disabled via API")
    
    return {"ok": True, "message": "Trading disabled"}


# ============================================================================
# HEARTBEAT TASK
# ============================================================================

async def heartbeat():
    """Periodic heartbeat"""
    print("💓 Heartbeat task started")
    logger.info("Heartbeat task started")
    await asyncio.sleep(5)  # Wait for initialization
    
    while True:
        try:
            if trader:
                win_rate = (trader.winning_trades / trader.total_trades * 100) if trader.total_trades > 0 else 0
                market_status = "🟢 OPEN" if trader.is_market_open() else "🔴 CLOSED"
                message = (
                    f"💓 Bot alive | "
                    f"Market: {market_status} | "
                    f"Positions: {len(trader.positions)} | "
                    f"Trades: {trader.total_trades} | "
                    f"Win Rate: {win_rate:.1f}% | "
                    f"Daily P&L: ${trader.daily_pnl:.2f}"
                )
                print(message)
                logger.info(message)
            else:
                print("💓 Heartbeat: Waiting for trader initialization...")
                logger.info("Heartbeat: Trader not initialized yet")
        except Exception as e:
            error_msg = f"Error in heartbeat: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
        
        await asyncio.sleep(60)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv('PORT', 10000))
    
    print("=" * 80)
    print("STARTING TRADING BOT APPLICATION")
    print("=" * 80)
    logger.info(f"Starting application on port {port}")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise