"""
Modular Autonomous Trading Bot
Uses separate strategy and trader components
"""

import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException
import uvicorn

from sma_crossover_strategy import SMACrossoverStrategy
from live_trader import LiveTrader
from config import settings


# ============================================================================
# FASTAPI APP FOR MONITORING
# ============================================================================

app = FastAPI(title="Trading Bot API")
trader: Optional[LiveTrader] = None


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "running",
        "strategy": trader.strategy.name if trader else None,
        "trading_enabled": trader.allow_trading if trader else False,
        "daily_pnl": trader.daily_pnl if trader else 0,
        "positions": len(trader.positions) if trader else 0,
        "total_trades": trader.total_trades if trader else 0
    }


@app.get("/positions")
def get_positions():
    """Get current positions"""
    if not trader:
        return {"positions": []}
    
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
        return {}
    
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
    if token != "let-me-in":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if trader:
        trader.allow_trading = False
        print("🚨 EMERGENCY STOP: Trading disabled via API")
    
    return {"ok": True, "message": "Trading disabled"}


@app.get("/")
def root():
    """API root"""
    return {
        "app": "Trading Bot",
        "version": "2.0",
        "mode": "paper" if settings.paper else "live",
        "endpoints": {
            "health": "/health",
            "positions": "/positions",
            "stats": "/stats",
            "kill": "POST /kill?token=let-me-in"
        }
    }


# ============================================================================
# ASYNC TASKS
# ============================================================================

async def run_http():
    """Run FastAPI server"""
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=10000, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def heartbeat():
    """Periodic heartbeat"""
    while True:
        if trader:
            win_rate = (trader.winning_trades / trader.total_trades * 100) if trader.total_trades > 0 else 0
            print(
                f"💓 Bot alive | "
                f"Positions: {len(trader.positions)} | "
                f"Trades: {trader.total_trades} | "
                f"Win Rate: {win_rate:.1f}% | "
                f"Daily P&L: ${trader.daily_pnl:.2f}"
            )
        await asyncio.sleep(60)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    global trader
    
    print("\n" + "="*80)
    print("🚀 INITIALIZING TRADING BOT")
    print("="*80)
    
    # Parse symbols
    symbols = settings.symbols
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(',')]
    
    print(f"📋 Configuration:")
    print(f"   Mode: {'PAPER' if settings.paper else 'LIVE'}")
    print(f"   Trading: {'ENABLED' if settings.allow_trading else 'DISABLED'}")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Data Feed: {settings.feed.upper()}")
    print(f"   Max Position: ${settings.max_usd_per_order}")
    print(f"   Max Daily Loss: ${settings.max_daily_loss}")
    print(f"   Strategy: SMA Crossover ({settings.short_window}/{settings.long_window})")
    print("="*80 + "\n")
    
    # Create strategy
    strategy = SMACrossoverStrategy(
        short_window=settings.short_window,
        long_window=settings.long_window,
        volume_threshold=settings.volume_threshold,
        stop_loss_pct=settings.stop_loss_pct
    )
    
    # Create trader
    trader = LiveTrader(strategy)
    
    print("✅ Bot initialized successfully")
    print(f"🌐 API will be available at http://0.0.0.0:10000")
    print(f"📊 Health check: http://0.0.0.0:10000/health\n")
    
    # Run everything together
    await asyncio.gather(
        run_http(),
        trader.run(symbols),
        heartbeat()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        raise