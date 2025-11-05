"""
Modular Autonomous Trading Bot with Editable Settings
"""

import os
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
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

# ============================================================================
# HTML DASHBOARD WITH SETTINGS
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header h1 { color: #333; font-size: 2.5em; margin-bottom: 10px; }
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .status-running { background: #10b981; color: white; }
        .status-disabled { background: #f59e0b; color: white; }
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
        .settings-panel {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .settings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            color: #555;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 1em;
            transition: border 0.3s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-group .hint {
            font-size: 0.85em;
            color: #888;
            margin-top: 5px;
        }
        .controls {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
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
        .market-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-left: 10px;
        }
        .market-open { background: #d1fae5; color: #065f46; }
        .market-closed { background: #fee2e2; color: #991b1b; }
        .dot { width: 10px; height: 10px; border-radius: 50%; }
        .dot-green { background: #10b981; }
        .dot-red { background: #ef4444; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .timestamp { text-align: right; color: #888; font-size: 0.9em; margin-top: 20px; }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: 500;
        }
        .alert-success { background: #d1fae5; color: #065f46; }
        .alert-error { background: #fee2e2; color: #991b1b; }
        .alert-warning { background: #fef3c7; color: #92400e; }
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider { background-color: #10b981; }
        input:checked + .slider:before { transform: translateX(26px); }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 12px 24px;
            background: #f3f4f6;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .tab.active {
            background: #667eea;
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Trading Bot Dashboard</h1>
            <div style="margin-top: 15px;">
                <span id="statusBadge" class="status-badge">Loading...</span>
                <span id="marketIndicator" class="market-indicator">
                    <span class="dot dot-green"></span>
                    <span>Loading...</span>
                </span>
            </div>
        </div>
        
        <div id="alertContainer"></div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('overview')">📊 Overview</button>
            <button class="tab" onclick="switchTab('settings')">⚙️ Settings</button>
        </div>
        
        <!-- OVERVIEW TAB -->
        <div id="overviewTab" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h3>Strategy</h3>
                    <div class="value" id="strategy">--</div>
                    <div class="subvalue">Active Trading Algorithm</div>
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
                <div id="positionsContent"><div class="loading">No open positions</div></div>
            </div>
            
            <div class="controls">
                <h2 style="margin-bottom: 20px; color: #333;">Quick Actions</h2>
                <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh Data</button>
                <button class="btn btn-danger" onclick="emergencyStop()">🚨 Emergency Stop</button>
                <div class="timestamp" id="lastUpdate">Last updated: --</div>
            </div>
        </div>
        
        <!-- SETTINGS TAB -->
        <div id="settingsTab" class="tab-content">
            <div class="settings-panel">
                <h2 style="margin-bottom: 20px; color: #333;">Bot Configuration</h2>
                <p style="color: #666; margin-bottom: 30px;">Adjust trading parameters. Changes apply immediately and will restart the bot with new settings.</p>
                
                <div class="settings-grid">
                    <div class="form-group">
                        <label>
                            Enable Trading
                            <label class="toggle-switch" style="float: right;">
                                <input type="checkbox" id="allowTrading">
                                <span class="slider"></span>
                            </label>
                        </label>
                        <div class="hint">⚠️ When enabled, bot will place real orders</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Symbols to Trade</label>
                        <input type="text" id="symbols" placeholder="AAPL,MSFT,GOOGL">
                        <div class="hint">Comma-separated list of stock symbols</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Max USD Per Order</label>
                        <input type="number" id="maxUsdPerOrder" min="10" max="10000" step="10">
                        <div class="hint">Maximum position size in dollars</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Max Daily Loss</label>
                        <input type="number" id="maxDailyLoss" min="10" max="1000" step="10">
                        <div class="hint">Trading stops if daily loss exceeds this</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Short SMA Window</label>
                        <input type="number" id="shortWindow" min="2" max="50" step="1">
                        <div class="hint">Number of periods for short moving average</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Long SMA Window</label>
                        <input type="number" id="longWindow" min="5" max="200" step="1">
                        <div class="hint">Number of periods for long moving average</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Volume Threshold</label>
                        <input type="number" id="volumeThreshold" min="1.0" max="5.0" step="0.1">
                        <div class="hint">Minimum volume multiplier (e.g., 1.5 = 1.5x avg)</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Stop Loss %</label>
                        <input type="number" id="stopLossPct" min="0.01" max="0.20" step="0.01">
                        <div class="hint">Stop loss percentage (0.02 = 2%)</div>
                    </div>
                </div>
                
                <div style="margin-top: 30px;">
                    <button class="btn btn-success" onclick="saveSettings()">💾 Save & Apply Settings</button>
                    <button class="btn btn-warning" onclick="loadSettings()">🔄 Reset to Current</button>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #fef3c7; border-radius: 8px; color: #92400e;">
                    <strong>⚠️ Important:</strong> Saving settings will restart the trading bot with new parameters. 
                    Any open positions will remain, but signal history will reset.
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentSettings = {};
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            if (tabName === 'settings') {
                loadSettings();
            }
        }
        
        function showAlert(message, type = 'success') {
            const container = document.getElementById('alertContainer');
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.textContent = message;
            container.appendChild(alert);
            
            setTimeout(() => alert.remove(), 5000);
        }
        
        async function fetchData() {
            try {
                const [health, stats, positions] = await Promise.all([
                    fetch('/health').then(r => r.json()),
                    fetch('/stats').then(r => r.json()),
                    fetch('/positions').then(r => r.json())
                ]);
                updateDashboard(health, stats, positions);
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function loadSettings() {
            try {
                const response = await fetch('/settings');
                currentSettings = await response.json();
                
                document.getElementById('allowTrading').checked = currentSettings.allow_trading;
                document.getElementById('symbols').value = currentSettings.symbols;
                document.getElementById('maxUsdPerOrder').value = currentSettings.max_usd_per_order;
                document.getElementById('maxDailyLoss').value = currentSettings.max_daily_loss;
                document.getElementById('shortWindow').value = currentSettings.short_window;
                document.getElementById('longWindow').value = currentSettings.long_window;
                document.getElementById('volumeThreshold').value = currentSettings.volume_threshold;
                document.getElementById('stopLossPct').value = currentSettings.stop_loss_pct;
            } catch (error) {
                showAlert('Failed to load settings', 'error');
            }
        }
        
        async function saveSettings() {
            const newSettings = {
                allow_trading: document.getElementById('allowTrading').checked,
                symbols: document.getElementById('symbols').value,
                max_usd_per_order: parseFloat(document.getElementById('maxUsdPerOrder').value),
                max_daily_loss: parseFloat(document.getElementById('maxDailyLoss').value),
                short_window: parseInt(document.getElementById('shortWindow').value),
                long_window: parseInt(document.getElementById('longWindow').value),
                volume_threshold: parseFloat(document.getElementById('volumeThreshold').value),
                stop_loss_pct: parseFloat(document.getElementById('stopLossPct').value)
            };
            
            if (!confirm('This will restart the bot with new settings. Continue?')) {
                return;
            }
            
            try {
                const response = await fetch('/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newSettings)
                });
                
                if (response.ok) {
                    showAlert('✅ Settings saved! Bot is restarting...', 'success');
                    setTimeout(() => {
                        switchTab('overview');
                        fetchData();
                    }, 2000);
                } else {
                    const error = await response.json();
                    showAlert('❌ Failed to save: ' + error.detail, 'error');
                }
            } catch (error) {
                showAlert('❌ Error saving settings', 'error');
            }
        }
        
        function updateDashboard(health, stats, positions) {
            const statusBadge = document.getElementById('statusBadge');
            if (health.trading_enabled) {
                statusBadge.textContent = '✅ Trading Enabled';
                statusBadge.className = 'status-badge status-running';
            } else {
                statusBadge.textContent = '💤 Trading Disabled';
                statusBadge.className = 'status-badge status-disabled';
            }
            
            const marketIndicator = document.getElementById('marketIndicator');
            if (health.market_open) {
                marketIndicator.innerHTML = '<span class="dot dot-green"></span><span>Market Open</span>';
                marketIndicator.className = 'market-indicator market-open';
            } else {
                marketIndicator.innerHTML = '<span class="dot dot-red"></span><span>Market Closed</span>';
                marketIndicator.className = 'market-indicator market-closed';
            }
            
            document.getElementById('strategy').textContent = health.strategy || 'N/A';
            
            const pnl = stats.daily_pnl || 0;
            const pnlEl = document.getElementById('dailyPnl');
            pnlEl.textContent = `$${pnl.toFixed(2)}`;
            pnlEl.className = 'value ' + (pnl >= 0 ? 'positive' : 'negative');
            
            document.getElementById('totalTrades').textContent = stats.total_trades || 0;
            document.getElementById('winRate').textContent = (stats.win_rate || 0) + '%';
            document.getElementById('positionCount').textContent = health.positions || 0;
            
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
                positionsContent.innerHTML = '<div class="loading">No open positions</div>';
            }
            
            document.getElementById('lastUpdate').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        }
        
        function refreshData() { fetchData(); }
        
        async function emergencyStop() {
            if (!confirm('Stop trading immediately?')) return;
            const token = prompt('Enter token (default: let-me-in):');
            if (!token) return;
            try {
                const response = await fetch(`/kill?token=${token}`, { method: 'POST' });
                if (response.ok) {
                    showAlert('✅ Trading stopped!', 'success');
                    fetchData();
                } else {
                    showAlert('❌ Invalid token', 'error');
                }
            } catch (error) {
                showAlert('❌ Error: ' + error.message, 'error');
            }
        }
        
        fetchData();
        setInterval(fetchData, 10000);
    </script>
</body>
</html>
"""


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
    global trading_task, heartbeat_task
    
    print("\n🛑 Shutting down...")
    if trading_task:
        trading_task.cancel()
    if heartbeat_task:
        heartbeat_task.cancel()
    print("✅ Shutdown complete")


async def initialize_bot():
    """Initialize or reinitialize the bot"""
    global trader, trading_task, heartbeat_task
    
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
    
    symbols = runtime_settings["symbols"]
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(',')]
    
    port = int(os.getenv('PORT', 10000))
    
    print(f"📋 Configuration:")
    print(f"   Mode: {'PAPER' if settings.paper else 'LIVE'}")
    print(f"   Trading: {'ENABLED' if runtime_settings['allow_trading'] else 'DISABLED'}")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Max Position: ${runtime_settings['max_usd_per_order']}")
    print(f"   Max Daily Loss: ${runtime_settings['max_daily_loss']}")
    print(f"   Strategy: SMA ({runtime_settings['short_window']}/{runtime_settings['long_window']})")
    print(f"   Dashboard: http://0.0.0.0:{port}")
    print("="*80 + "\n")
    
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
                message = (
                    f"💓 Bot alive | "
                    f"Market: {market_status} | "
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
    print("STARTING TRADING BOT APPLICATION")
    print("=" * 80)
    logger.info(f"Starting application on port {port}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise