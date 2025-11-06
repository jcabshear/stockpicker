"""
Modular Autonomous Trading Bot with Auto Stock Selection
Now automatically picks the top 3 stocks daily based on multi-factor scoring
"""

import os
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Import after creating files
import sys
sys.path.insert(0, '/home/claude')

from config import settings

# Dynamic imports to handle file creation
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

# Editable settings (runtime overrides)
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

# ============================================================================
# HTML DASHBOARD (Updated with auto-selection info)
# ============================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #e0e7ff;
            min-height: 100vh;
            padding: 20px;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.1) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(168, 85, 247, 0.1) 0px, transparent 50%);
        }
        
        .container { max-width: 1400px; margin: 0 auto; }
        
        .header {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(99, 102, 241, 0.2);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 25px;
            box-shadow: 
                0 0 40px rgba(99, 102, 241, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        .header h1 { 
            color: #f0f9ff; 
            font-size: 2.5em; 
            margin-bottom: 15px;
            font-weight: 700;
            letter-spacing: -1px;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .status-running { background: #10b981; color: white; }
        .status-disabled { background: #f59e0b; color: white; }
        .status-auto { background: #3b82f6; color: white; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h3 {
            color: #555;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .card .value { font-size: 2em; font-weight: bold; color: #333; }
        .card .subvalue { color: #888; font-size: 0.9em; margin-top: 5px; }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        .positions-table {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
            overflow-x: auto;
        }
        table { width: 100%; border-collapse: collapse; }
        th {
            text-align: left;
            padding: 15px;
            color: #555;
            font-weight: 600;
            border-bottom: 2px solid #e5e7eb;
        }
        td { padding: 15px; border-bottom: 1px solid #e5e7eb; }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            margin-right: 10px;
            margin-bottom: 10px;
            transition: all 0.3s;
            font-size: 1em;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .btn-primary { background: #667eea; color: white; }
        .btn-success { background: #10b981; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-warning { background: #f59e0b; color: white; }
        .auto-select-info {
            background: #dbeafe;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #3b82f6;
        }
        .auto-select-info strong { color: #1e40af; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Trading Bot Dashboard</h1>
            <div style="margin-top: 15px;">
                <span id="statusBadge" class="status-badge">Loading...</span>
                <span id="autoSelectBadge" class="status-badge status-auto" style="display:none;">🎯 Auto-Select</span>
            </div>
            <div id="autoSelectInfo" class="auto-select-info" style="display:none;">
                <strong>🎯 Auto Stock Selection Active</strong><br>
                Bot automatically picks top 3 stocks daily based on multi-factor scoring
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Current Symbols</h3>
                <div class="value" id="symbols" style="font-size:1.5em;">--</div>
                <div class="subvalue" id="symbolsSource">Loading...</div>
            </div>
            <div class="card">
                <h3>Daily P&L</h3>
                <div class="value" id="dailyPnl">$0.00</div>
                <div class="subvalue">Today's Performance</div>
            </div>
            <div class="card">
                <h3>Total Trades</h3>
                <div class="value" id="totalTrades">0</div>
                <div class="subvalue"><span id="winRate">0%</span> Win Rate</div>
            </div>
            <div class="card">
                <h3>Open Positions</h3>
                <div class="value" id="positionCount">0</div>
                <div class="subvalue">Active Trades</div>
            </div>
        </div>
        
        <div class="positions-table">
            <h2 style="margin-bottom: 20px; color: #333;">Current Positions</h2>
            <div id="positionsContent"><div style="text-align:center;padding:40px;">No open positions</div></div>
        </div>
    </div>
    
    <script>
        async function fetchData() {
            try {
                const [health, stats, positions, settings] = await Promise.all([
                    fetch('/health').then(r => r.json()),
                    fetch('/stats').then(r => r.json()),
                    fetch('/positions').then(r => r.json()),
                    fetch('/settings').then(r => r.json())
                ]);
                updateDashboard(health, stats, positions, settings);
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        function updateDashboard(health, stats, positions, settings) {
            // Status badge
            const statusBadge = document.getElementById('statusBadge');
            if (health.trading_enabled) {
                statusBadge.textContent = '✅ Trading Enabled';
                statusBadge.className = 'status-badge status-running';
            } else {
                statusBadge.textContent = '💤 Trading Disabled';
                statusBadge.className = 'status-badge status-disabled';
            }
            
            // Auto-select badge
            if (settings.auto_select_stocks) {
                document.getElementById('autoSelectBadge').style.display = 'inline-block';
                document.getElementById('autoSelectInfo').style.display = 'block';
            }
            
            // Symbols
            const symbolsEl = document.getElementById('symbols');
            const symbolsSourceEl = document.getElementById('symbolsSource');
            if (settings.symbols) {
                symbolsEl.textContent = settings.symbols.replace(/,/g, ', ');
                if (settings.auto_select_stocks) {
                    symbolsSourceEl.textContent = '🎯 Auto-selected daily (score ≥' + settings.min_stock_score + ')';
                } else {
                    symbolsSourceEl.textContent = 'Manually configured';
                }
            }
            
            // P&L
            const pnl = stats.daily_pnl || 0;
            const pnlEl = document.getElementById('dailyPnl');
            pnlEl.textContent = `$${pnl.toFixed(2)}`;
            pnlEl.className = 'value ' + (pnl >= 0 ? 'positive' : 'negative');
            
            // Stats
            document.getElementById('totalTrades').textContent = stats.total_trades || 0;
            document.getElementById('winRate').textContent = (stats.win_rate || 0) + '%';
            document.getElementById('positionCount').textContent = health.positions || 0;
            
            // Positions
            const positionsContent = document.getElementById('positionsContent');
            if (positions.positions && positions.positions.length > 0) {
                let tableHTML = '<table><thead><tr><th>Symbol</th><th>Shares</th><th>Entry</th><th>Current</th><th>P&L</th><th>P&L %</th></tr></thead><tbody>';
                positions.positions.forEach(pos => {
                    const pnlClass = pos.pnl >= 0 ? 'positive' : 'negative';
                    tableHTML += `<tr>
                        <td><strong>${pos.symbol}</strong></td>
                        <td>${pos.shares.toFixed(2)}</td>
                        <td>$${pos.entry_price.toFixed(2)}</td>
                        <td>$${pos.current_price.toFixed(2)}</td>
                        <td class="${pnlClass}">$${pos.pnl.toFixed(2)}</td>
                        <td class="${pnlClass}">${pos.pnl_pct.toFixed(2)}%</td>
                    </tr>`;
                });
                tableHTML += '</tbody></table>';
                positionsContent.innerHTML = tableHTML;
            } else {
                positionsContent.innerHTML = '<div style="text-align:center;padding:40px;">No open positions</div>';
            }
        }
        
        fetchData();
        setInterval(fetchData, 10000); // Refresh every 10 seconds
    </script>
</body>
</html>
"""

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Trading Bot API with Auto Stock Selection")


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
    global runtime_settings, trader
    
    print(f"\n📊 Updating trading symbols: {', '.join(new_symbols)}")
    runtime_settings["symbols"] = ','.join(new_symbols)
    
    # Restart trader with new symbols
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
        
        # Get current best stocks
        symbols = stock_selector.get_current_symbols()
        runtime_settings["symbols"] = ','.join(symbols)
        
        print(f"   Selected stocks: {', '.join(symbols)}")
        print(f"   Min score threshold: {runtime_settings.get('min_stock_score', 60)}")
        
        # Start auto-selection background task
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
    
    # Import strategy and trader here to handle missing files
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


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard"""
    return DASHBOARD_HTML


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


@app.get("/settings")
def get_settings():
    """Get current settings"""
    return runtime_settings


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
# HEARTBEAT TASK
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