"""
Dashboard HTML Templates
Complete dashboard.py with comprehensive backtesting
"""

# Import the enhanced backtest HTML
import sys
sys.path.insert(0, '/home/claude')

# Main dashboard HTML (unchanged from original)
MAIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Dashboard</title>
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #1a1a2e;
            min-height: 100vh;
            padding: 0;
        }
        
        .container { 
            max-width: 1400px; 
            margin: 0 auto;
            padding: 0;
        }
        
        /* Header */
        .header {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            padding: 24px 40px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo-section h1 { 
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
            color: #1a1a2e;
            margin-bottom: 4px;
        }
        
        .tagline {
            font-size: 14px;
            color: #666;
            font-weight: 400;
        }
        
        .header-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .settings-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
        }
        
        .settings-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .status-section {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 0.3px;
            transition: all 0.3s;
        }
        
        .status-badge::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .status-running { 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white; 
        }
        .status-running::before { background: white; }
        
        .status-disabled { 
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white; 
        }
        .status-disabled::before { background: white; }
        
        .status-auto { 
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white; 
        }
        .status-auto::before { background: white; }
        
        /* Toggle Switch */
        .toggle-container {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 20px;
            border-radius: 24px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .toggle-label {
            font-weight: 600;
            font-size: 14px;
            color: #374151;
        }
        
        .toggle-switch {
            position: relative;
            width: 56px;
            height: 28px;
            cursor: pointer;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .toggle-slider {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: #cbd5e1;
            border-radius: 28px;
            transition: all 0.3s;
        }
        
        .toggle-slider:before {
            content: '';
            position: absolute;
            height: 20px;
            width: 20px;
            left: 4px;
            bottom: 4px;
            background: white;
            border-radius: 50%;
            transition: all 0.3s;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .toggle-switch input:checked + .toggle-slider {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }
        
        .toggle-switch input:checked + .toggle-slider:before {
            transform: translateX(28px);
        }
        
        /* Main Content */
        .main-content {
            padding: 32px 40px;
        }
        
        /* Account Stats Section */
        .account-section {
            background: rgba(255, 255, 255, 0.95);
            padding: 24px 28px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.06);
        }
        
        .account-header {
            font-size: 18px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .account-status {
            font-size: 13px;
            font-weight: 600;
            color: #6b7280;
        }
        
        .account-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .account-stat {
            display: flex;
            flex-direction: column;
        }
        
        .account-stat-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: #6b7280;
            font-weight: 600;
            margin-bottom: 6px;
        }
        
        .account-stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #1a1a2e;
        }
        
        /* Banners */
        .warning-banner {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 24px;
            border-radius: 16px;
            margin-bottom: 24px;
            border-left: 4px solid #f59e0b;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }
        
        .warning-banner strong {
            color: #d97706;
            font-weight: 600;
        }
        
        .warning-banner p {
            color: #4b5563;
            line-height: 1.6;
            margin-top: 4px;
        }
        
        .info-banner {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 24px;
            border-radius: 16px;
            margin-bottom: 24px;
            border-left: 4px solid #3b82f6;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }
        
        .info-banner strong {
            color: #1e40af;
            font-weight: 600;
        }
        
        .info-banner p {
            color: #4b5563;
            line-height: 1.6;
            margin-top: 4px;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid rgba(0, 0, 0, 0.06);
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }
        
        .stat-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #6b7280;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 4px;
        }
        
        .stat-subvalue {
            font-size: 13px;
            color: #9ca3af;
            font-weight: 500;
        }
        
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        
        /* Positions Table */
        .positions-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.06);
        }
        
        .section-header {
            font-size: 20px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 20px;
            letter-spacing: -0.3px;
        }
        
        table { 
            width: 100%; 
            border-collapse: separate;
            border-spacing: 0;
        }
        
        thead {
            background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
        }
        
        th {
            text-align: left;
            padding: 16px;
            color: #6b7280;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            border-bottom: 2px solid #e5e7eb;
        }
        
        th:first-child { border-radius: 12px 0 0 0; }
        th:last-child { border-radius: 0 12px 0 0; }
        
        td { 
            padding: 18px 16px; 
            border-bottom: 1px solid #f3f4f6;
            font-size: 14px;
            color: #374151;
        }
        
        tbody tr {
            transition: background 0.2s;
        }
        
        tbody tr:hover {
            background: #f9fafb;
        }
        
        tbody tr:last-child td {
            border-bottom: none;
        }
        
        .symbol-cell {
            font-weight: 700;
            color: #1a1a2e;
            font-size: 15px;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #9ca3af;
        }
        
        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 12px;
            opacity: 0.3;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                align-items: flex-start;
                gap: 16px;
            }
            
            .header-actions {
                flex-wrap: wrap;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .main-content {
                padding: 20px;
            }
            
            .positions-section {
                overflow-x: auto;
            }
            
            table {
                min-width: 600px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    <h1>Trading Dashboard</h1>
                    <div class="tagline">Algorithmic Trading System • Paper Account</div>
                </div>
                <div class="header-actions">
                    <div class="toggle-container">
                        <span class="toggle-label">Trading</span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="tradingToggle">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <span id="statusBadge" class="status-badge">Loading...</span>
                    <span id="autoSelectBadge" class="status-badge status-auto" style="display:none;">Auto-Select</span>
                    <a href="/backtest" class="settings-btn">📊 Backtest</a>
                    <a href="/settings" class="settings-btn">⚙️ Settings</a>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div id="warningBanner" class="warning-banner" style="display:none;">
                <strong>⚠️ Trading Disabled</strong>
                <p>The bot is monitoring only. Enable the toggle above to allow trade execution.</p>
            </div>
            
            <div id="infoBanner" class="info-banner">
                <strong>Intelligent Stock Selection Active</strong>
                <p>System automatically analyzes and selects optimal trading opportunities daily based on multi-factor technical analysis.</p>
            </div>
            
            <!-- Account Section -->
            <div class="account-section">
                <div class="account-header">
                    Alpaca Account
                    <span class="account-status" id="accountStatus">Loading...</span>
                </div>
                <div class="account-grid">
                    <div class="account-stat">
                        <div class="account-stat-label">Portfolio Value</div>
                        <div class="account-stat-value" id="portfolioValue">$0.00</div>
                    </div>
                    <div class="account-stat">
                        <div class="account-stat-label">Buying Power</div>
                        <div class="account-stat-value" id="buyingPower">$0.00</div>
                    </div>
                    <div class="account-stat">
                        <div class="account-stat-label">Cash</div>
                        <div class="account-stat-value" id="cash">$0.00</div>
                    </div>
                    <div class="account-stat">
                        <div class="account-stat-label">Today's P&L</div>
                        <div class="account-stat-value" id="todayPnl">$0.00</div>
                    </div>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Active Symbols</div>
                    <div class="stat-value" id="symbols" style="font-size: 20px; line-height: 1.3;">--</div>
                    <div class="stat-subvalue" id="symbolsSource">Loading...</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Bot Daily P&L</div>
                    <div class="stat-value" id="dailyPnl">$0.00</div>
                    <div class="stat-subvalue">Today's Performance</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Trades</div>
                    <div class="stat-value" id="totalTrades">0</div>
                    <div class="stat-subvalue"><span id="winRate">0%</span> Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Open Positions</div>
                    <div class="stat-value" id="positionCount">0</div>
                    <div class="stat-subvalue">Active Trades</div>
                </div>
            </div>
            
            <div class="positions-section">
                <h2 class="section-header">Current Positions</h2>
                <div id="positionsContent">
                    <div class="empty-state">
                        <div class="empty-state-icon">📊</div>
                        <div>No open positions</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let isUpdatingToggle = false;
        
        async function fetchData() {
            try {
                const [health, stats, positions, settings, account] = await Promise.all([
                    fetch('/health').then(r => r.json()),
                    fetch('/stats').then(r => r.json()),
                    fetch('/positions').then(r => r.json()),
                    fetch('/api/settings').then(r => r.json()),
                    fetch('/account').then(r => r.json())
                ]);
                updateDashboard(health, stats, positions, settings, account);
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        function updateDashboard(health, stats, positions, settings, account) {
            // Update toggle
            const toggle = document.getElementById('tradingToggle');
            const shouldBeChecked = health.trading_enabled;
            
            if (toggle.checked !== shouldBeChecked && !isUpdatingToggle) {
                toggle.checked = shouldBeChecked;
            }
            
            // Status badge
            const statusBadge = document.getElementById('statusBadge');
            if (health.trading_enabled) {
                statusBadge.textContent = 'Trading Active';
                statusBadge.className = 'status-badge status-running';
                document.getElementById('warningBanner').style.display = 'none';
            } else {
                statusBadge.textContent = 'Monitoring Only';
                statusBadge.className = 'status-badge status-disabled';
                document.getElementById('warningBanner').style.display = 'block';
            }
            
            // Auto-select badge
            if (settings.auto_select_stocks) {
                document.getElementById('autoSelectBadge').style.display = 'inline-flex';
                document.getElementById('infoBanner').style.display = 'block';
            }
            
            // Account data
            if (account && account.equity) {
                document.getElementById('portfolioValue').textContent = `$${parseFloat(account.equity).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                document.getElementById('buyingPower').textContent = `$${parseFloat(account.buying_power).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                document.getElementById('cash').textContent = `$${parseFloat(account.cash).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                
                const todayPnl = parseFloat(account.today_pnl || 0);
                const todayPnlEl = document.getElementById('todayPnl');
                todayPnlEl.textContent = `$${todayPnl.toFixed(2)}`;
                todayPnlEl.className = 'account-stat-value ' + (todayPnl >= 0 ? 'positive' : 'negative');
                
                document.getElementById('accountStatus').textContent = account.status || 'Active';
            }
            
            // Symbols
            const symbolsEl = document.getElementById('symbols');
            const symbolsSourceEl = document.getElementById('symbolsSource');
            if (settings.symbols) {
                symbolsEl.textContent = settings.symbols.replace(/,/g, ', ');
                if (settings.auto_select_stocks) {
                    symbolsSourceEl.textContent = 'Auto-selected (Min Score: ' + settings.min_stock_score + ')';
                } else {
                    symbolsSourceEl.textContent = 'Manually configured';
                }
            }
            
            // Bot P&L
            const pnl = stats.daily_pnl || 0;
            const pnlEl = document.getElementById('dailyPnl');
            pnlEl.textContent = `$${pnl.toFixed(2)}`;
            pnlEl.className = 'stat-value ' + (pnl >= 0 ? 'positive' : 'negative');
            
            // Stats
            document.getElementById('totalTrades').textContent = stats.total_trades || 0;
            document.getElementById('winRate').textContent = (stats.win_rate || 0) + '%';
            document.getElementById('positionCount').textContent = health.positions || 0;
            
            // Positions
            const positionsContent = document.getElementById('positionsContent');
            if (positions.positions && positions.positions.length > 0) {
                let tableHTML = '<table><thead><tr><th>Symbol</th><th>Shares</th><th>Entry Price</th><th>Current Price</th><th>P&L</th><th>P&L %</th></tr></thead><tbody>';
                positions.positions.forEach(pos => {
                    const pnlClass = pos.pnl >= 0 ? 'positive' : 'negative';
                    tableHTML += `<tr>
                        <td class="symbol-cell">${pos.symbol}</td>
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
                positionsContent.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📊</div><div>No open positions</div></div>';
            }
        }
        
        // Toggle handler
        document.getElementById('tradingToggle').addEventListener('change', async function(e) {
            if (isUpdatingToggle) return;
            
            isUpdatingToggle = true;
            const enabled = e.target.checked;
            
            try {
                const response = await fetch('/toggle-trading', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: enabled })
                });
                
                if (!response.ok) throw new Error('Failed to toggle trading');
                
                await fetchData();
            } catch (error) {
                console.error('Error toggling trading:', error);
                e.target.checked = !enabled;
                alert('Failed to toggle trading. Please try again.');
            } finally {
                isUpdatingToggle = false;
            }
        });
        
        fetchData();
        setInterval(fetchData, 10000);
    </script>
</body>
</html>
"""

# Settings page HTML (unchanged)
SETTINGS_PAGE_HTML = """
[... keeping original settings page HTML from document ...]
"""

# COMPREHENSIVE BACKTEST PAGE - Load from external file
# This is too large to inline, so we'll load it dynamically
try:
    from enhanced_backtest_page import ENHANCED_BACKTEST_HTML as BACKTEST_PAGE_HTML
except ImportError:
    # Fallback to original if enhanced version not available
    BACKTEST_PAGE_HTML = """
    [... original backtest page ...]
    """