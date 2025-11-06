"""
Dashboard HTML Templates
Separated for cleaner code organization
"""

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

SETTINGS_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - Trading Dashboard</title>
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
            max-width: 900px; 
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
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .back-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
        }
        
        .back-btn:hover {
            background: rgba(102, 126, 234, 0.2);
            transform: translateX(-2px);
        }
        
        h1 {
            font-size: 28px;
            font-weight: 700;
            color: #1a1a2e;
        }
        
        /* Main Content */
        .main-content {
            padding: 32px 40px;
        }
        
        .settings-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.06);
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f3f4f6;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        .form-label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
        }
        
        .form-help {
            font-size: 13px;
            color: #6b7280;
            margin-top: 4px;
        }
        
        .form-input {
            width: 100%;
            padding: 12px 16px;
            font-size: 14px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            transition: all 0.3s;
            font-family: inherit;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .form-checkbox {
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
        }
        
        .form-checkbox input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        .btn-primary {
            display: inline-block;
            padding: 14px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .success-message {
            background: #d1fae5;
            color: #065f46;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
        }
        
        .error-message {
            background: #fee2e2;
            color: #991b1b;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>⚙️ Settings</h1>
                <a href="/" class="back-btn">← Back to Dashboard</a>
            </div>
        </div>
        
        <div class="main-content">
            <div id="successMessage" class="success-message"></div>
            <div id="errorMessage" class="error-message"></div>
            
            <form id="settingsForm">
                <!-- Strategy Settings -->
                <div class="settings-section">
                    <h2 class="section-title">Strategy Parameters</h2>
                    
                    <div class="form-group">
                        <label class="form-label">Short SMA Window</label>
                        <input type="number" class="form-input" id="shortWindow" min="2" max="50" required>
                        <div class="form-help">Number of periods for short-term moving average (2-50)</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Long SMA Window</label>
                        <input type="number" class="form-input" id="longWindow" min="5" max="200" required>
                        <div class="form-help">Number of periods for long-term moving average (5-200)</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Volume Threshold</label>
                        <input type="number" class="form-input" id="volumeThreshold" min="1" max="5" step="0.1" required>
                        <div class="form-help">Minimum volume multiplier for entry signals (1.0 = average volume)</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Stop Loss %</label>
                        <input type="number" class="form-input" id="stopLossPct" min="0.01" max="0.5" step="0.01" required>
                        <div class="form-help">Stop loss percentage (0.02 = 2%)</div>
                    </div>
                </div>
                
                <!-- Risk Management -->
                <div class="settings-section">
                    <h2 class="section-title">Risk Management</h2>
                    
                    <div class="form-group">
                        <label class="form-label">Max USD Per Order</label>
                        <input type="number" class="form-input" id="maxUsdPerOrder" min="10" max="10000" required>
                        <div class="form-help">Maximum position size in USD per trade</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Max Daily Loss</label>
                        <input type="number" class="form-input" id="maxDailyLoss" min="10" max="1000" required>
                        <div class="form-help">Maximum allowed loss per day (trading halts if exceeded)</div>
                    </div>
                </div>
                
                <!-- Stock Selection -->
                <div class="settings-section">
                    <h2 class="section-title">Stock Selection</h2>
                    
                    <div class="form-group">
                        <label class="form-checkbox">
                            <input type="checkbox" id="autoSelectStocks">
                            <span class="form-label" style="margin: 0;">Enable Auto Stock Selection</span>
                        </label>
                        <div class="form-help">Automatically select top stocks daily based on technical scoring</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Minimum Stock Score</label>
                        <input type="number" class="form-input" id="minStockScore" min="0" max="100" required>
                        <div class="form-help">Minimum technical score required for stock selection (0-100)</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Trading Symbols</label>
                        <input type="text" class="form-input" id="symbols" required>
                        <div class="form-help">Comma-separated list of symbols (ignored if auto-select is enabled)</div>
                    </div>
                </div>
                
                <!-- Trading Control -->
                <div class="settings-section">
                    <h2 class="section-title">Trading Control</h2>
                    
                    <div class="form-group">
                        <label class="form-checkbox">
                            <input type="checkbox" id="allowTrading">
                            <span class="form-label" style="margin: 0;">Enable Trading Execution</span>
                        </label>
                        <div class="form-help">Allow bot to execute trades (monitoring only when disabled)</div>
                    </div>
                </div>
                
                <button type="submit" class="btn-primary" id="saveBtn">Save Settings & Restart Bot</button>
            </form>
        </div>
    </div>
    
    <script>
        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                const settings = await response.json();
                
                document.getElementById('shortWindow').value = settings.short_window;
                document.getElementById('longWindow').value = settings.long_window;
                document.getElementById('volumeThreshold').value = settings.volume_threshold;
                document.getElementById('stopLossPct').value = settings.stop_loss_pct;
                document.getElementById('maxUsdPerOrder').value = settings.max_usd_per_order;
                document.getElementById('maxDailyLoss').value = settings.max_daily_loss;
                document.getElementById('autoSelectStocks').checked = settings.auto_select_stocks;
                document.getElementById('minStockScore').value = settings.min_stock_score;
                document.getElementById('symbols').value = settings.symbols;
                document.getElementById('allowTrading').checked = settings.allow_trading;
            } catch (error) {
                console.error('Error loading settings:', error);
                showError('Failed to load settings');
            }
        }
        
        function showSuccess(message) {
            const el = document.getElementById('successMessage');
            el.textContent = '✓ ' + message;
            el.style.display = 'block';
            setTimeout(() => el.style.display = 'none', 5000);
        }
        
        function showError(message) {
            const el = document.getElementById('errorMessage');
            el.textContent = '✗ ' + message;
            el.style.display = 'block';
            setTimeout(() => el.style.display = 'none', 5000);
        }
        
        document.getElementById('settingsForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const saveBtn = document.getElementById('saveBtn');
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';
            
            const settings = {
                short_window: parseInt(document.getElementById('shortWindow').value),
                long_window: parseInt(document.getElementById('longWindow').value),
                volume_threshold: parseFloat(document.getElementById('volumeThreshold').value),
                stop_loss_pct: parseFloat(document.getElementById('stopLossPct').value),
                max_usd_per_order: parseFloat(document.getElementById('maxUsdPerOrder').value),
                max_daily_loss: parseFloat(document.getElementById('maxDailyLoss').value),
                auto_select_stocks: document.getElementById('autoSelectStocks').checked,
                min_stock_score: parseFloat(document.getElementById('minStockScore').value),
                symbols: document.getElementById('symbols').value,
                allow_trading: document.getElementById('allowTrading').checked
            };
            
            try {
                const response = await fetch('/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to save settings');
                }
                
                showSuccess('Settings saved successfully! Bot is restarting...');
                setTimeout(() => window.location.href = '/', 2000);
            } catch (error) {
                console.error('Error saving settings:', error);
                showError(error.message);
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save Settings & Restart Bot';
            }
        });
        
        loadSettings();
    </script>
</body>
</html>
"""

BACKTEST_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest - Trading Dashboard</title>
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
            max-width: 1200px; 
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
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .back-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
        }
        
        .back-btn:hover {
            background: rgba(102, 126, 234, 0.2);
            transform: translateX(-2px);
        }
        
        h1 {
            font-size: 28px;
            font-weight: 700;
            color: #1a1a2e;
        }
        
        /* Main Content */
        .main-content {
            padding: 32px 40px;
        }
        
        .section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.06);
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f3f4f6;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 0;
        }
        
        .form-label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
        }
        
        .form-help {
            font-size: 13px;
            color: #6b7280;
            margin-top: 4px;
        }
        
        .form-input {
            width: 100%;
            padding: 12px 16px;
            font-size: 14px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            transition: all 0.3s;
            font-family: inherit;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn-primary {
            display: inline-block;
            padding: 14px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .loading-message {
            background: #dbeafe;
            color: #1e40af;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
        }
        
        .error-message {
            background: #fee2e2;
            color: #991b1b;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
        }
        
        /* Results Section */
        .results-section {
            display: none;
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .result-card {
            background: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
        }
        
        .result-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: #6b7280;
            font-weight: 600;
            margin-bottom: 6px;
        }
        
        .result-value {
            font-size: 28px;
            font-weight: 700;
            color: #1a1a2e;
        }
        
        .result-value.positive { color: #10b981; }
        .result-value.negative { color: #ef4444; }
        
        .trades-table {
            margin-top: 24px;
            overflow-x: auto;
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
            padding: 12px 16px;
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
            padding: 12px 16px;
            border-bottom: 1px solid #f3f4f6;
            font-size: 14px;
            color: #374151;
        }
        
        tbody tr:hover {
            background: #f9fafb;
        }
        
        .positive { color: #10b981; font-weight: 600; }
        .negative { color: #ef4444; font-weight: 600; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .form-grid {
                grid-template-columns: 1fr;
            }
            
            .results-grid {
                grid-template-columns: 1fr;
            }
            
            .main-content {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>📊 Backtest Strategy</h1>
                <a href="/" class="back-btn">← Back to Dashboard</a>
            </div>
        </div>
        
        <div class="main-content">
            <div id="loadingMessage" class="loading-message"></div>
            <div id="errorMessage" class="error-message"></div>
            
            <!-- Backtest Form -->
            <form id="backtestForm">
                <div class="section">
                    <h2 class="section-title">Strategy Parameters</h2>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Short SMA Window</label>
                            <input type="number" class="form-input" id="shortWindow" min="2" max="50" value="5" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Long SMA Window</label>
                            <input type="number" class="form-input" id="longWindow" min="5" max="200" value="20" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Volume Threshold</label>
                            <input type="number" class="form-input" id="volumeThreshold" min="1" max="5" step="0.1" value="1.5" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Stop Loss %</label>
                            <input type="number" class="form-input" id="stopLossPct" min="0.01" max="0.5" step="0.01" value="0.02" required>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">Backtest Parameters</h2>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Trading Symbols</label>
                            <input type="text" class="form-input" id="symbols" value="AAPL,MSFT,GOOGL" required>
                            <div class="form-help">Comma-separated list</div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Days to Test</label>
                            <input type="number" class="form-input" id="daysToTest" min="1" max="365" value="30" required>
                            <div class="form-help">Number of days to backtest</div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Initial Capital</label>
                            <input type="number" class="form-input" id="initialCapital" min="1000" max="1000000" value="10000" required>
                            <div class="form-help">Starting portfolio value</div>
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="btn-primary" id="runBtn">Run Backtest</button>
            </form>
            
            <!-- Results Section -->
            <div id="resultsSection" class="results-section">
                <div class="section">
                    <h2 class="section-title">Backtest Results</h2>
                    
                    <div class="results-grid">
                        <div class="result-card">
                            <div class="result-label">Total Return</div>
                            <div class="result-value" id="totalReturn">--</div>
                        </div>
                        <div class="result-card">
                            <div class="result-label">Final Value</div>
                            <div class="result-value" id="finalValue">--</div>
                        </div>
                        <div class="result-card">
                            <div class="result-label">Total Trades</div>
                            <div class="result-value" id="totalTrades">--</div>
                        </div>
                        <div class="result-card">
                            <div class="result-label">Win Rate</div>
                            <div class="result-value" id="winRate">--</div>
                        </div>
                        <div class="result-card">
                            <div class="result-label">Profit Factor</div>
                            <div class="result-value" id="profitFactor">--</div>
                        </div>
                        <div class="result-card">
                            <div class="result-label">Sharpe Ratio</div>
                            <div class="result-value" id="sharpeRatio">--</div>
                        </div>
                        <div class="result-card">
                            <div class="result-label">Max Drawdown</div>
                            <div class="result-value negative" id="maxDrawdown">--</div>
                        </div>
                        <div class="result-card">
                            <div class="result-label">Avg Win</div>
                            <div class="result-value positive" id="avgWin">--</div>
                        </div>
                        <div class="result-card">
                            <div class="result-label">Avg Loss</div>
                            <div class="result-value negative" id="avgLoss">--</div>
                        </div>
                    </div>
                    
                    <div class="trades-table">
                        <h3 style="margin-bottom: 16px; color: #1a1a2e;">Trade History</h3>
                        <div id="tradesContent"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('backtestForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const runBtn = document.getElementById('runBtn');
            const loadingMsg = document.getElementById('loadingMessage');
            const errorMsg = document.getElementById('errorMessage');
            const resultsSection = document.getElementById('resultsSection');
            
            // Hide previous results and errors
            resultsSection.style.display = 'none';
            errorMsg.style.display = 'none';
            
            // Show loading
            runBtn.disabled = true;
            runBtn.textContent = 'Running Backtest...';
            loadingMsg.textContent = 'Running backtest... This may take 30-60 seconds.';
            loadingMsg.style.display = 'block';
            
            const params = {
                short_window: parseInt(document.getElementById('shortWindow').value),
                long_window: parseInt(document.getElementById('longWindow').value),
                volume_threshold: parseFloat(document.getElementById('volumeThreshold').value),
                stop_loss_pct: parseFloat(document.getElementById('stopLossPct').value),
                symbols: document.getElementById('symbols').value,
                days: parseInt(document.getElementById('daysToTest').value),
                initial_capital: parseFloat(document.getElementById('initialCapital').value)
            };
            
            try {
                const response = await fetch('/api/backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Backtest failed');
                }
                
                const results = await response.json();
                displayResults(results);
                
                loadingMsg.style.display = 'none';
                resultsSection.style.display = 'block';
                
                // Scroll to results
                resultsSection.scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                console.error('Error:', error);
                errorMsg.textContent = '❌ ' + error.message;
                errorMsg.style.display = 'block';
                loadingMsg.style.display = 'none';
            } finally {
                runBtn.disabled = false;
                runBtn.textContent = 'Run Backtest';
            }
        });
        
        function displayResults(results) {
            // Update result cards
            const totalReturnEl = document.getElementById('totalReturn');
            totalReturnEl.textContent = results.total_return_pct.toFixed(2) + '%';
            totalReturnEl.className = 'result-value ' + (results.total_return_pct >= 0 ? 'positive' : 'negative');
            
            document.getElementById('finalValue').textContent = '$' + results.final_value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            document.getElementById('totalTrades').textContent = results.total_trades;
            document.getElementById('winRate').textContent = (results.win_rate * 100).toFixed(1) + '%';
            
            const pfEl = document.getElementById('profitFactor');
            pfEl.textContent = results.profit_factor.toFixed(2);
            pfEl.className = 'result-value ' + (results.profit_factor >= 1 ? 'positive' : 'negative');
            
            const srEl = document.getElementById('sharpeRatio');
            srEl.textContent = results.sharpe_ratio.toFixed(2);
            srEl.className = 'result-value ' + (results.sharpe_ratio >= 1 ? 'positive' : 'negative');
            
            document.getElementById('maxDrawdown').textContent = results.max_drawdown_pct.toFixed(2) + '%';
            document.getElementById('avgWin').textContent = '$' + results.avg_win.toFixed(2);
            document.getElementById('avgLoss').textContent = '$' + results.avg_loss.toFixed(2);
            
            // Display trades table
            const tradesContent = document.getElementById('tradesContent');
            if (results.trades && results.trades.length > 0) {
                let tableHTML = '<table><thead><tr><th>Symbol</th><th>Action</th><th>Shares</th><th>Price</th><th>P&L</th><th>P&L %</th><th>Timestamp</th></tr></thead><tbody>';
                
                results.trades.forEach(trade => {
                    if (trade.action === 'close') {
                        const pnlClass = trade.pnl >= 0 ? 'positive' : 'negative';
                        tableHTML += `<tr>
                            <td><strong>${trade.symbol}</strong></td>
                            <td>${trade.action.toUpperCase()}</td>
                            <td>${trade.shares.toFixed(2)}</td>
                            <td>$${trade.price.toFixed(2)}</td>
                            <td class="${pnlClass}">$${trade.pnl.toFixed(2)}</td>
                            <td class="${pnlClass}">${(trade.pnl_pct * 100).toFixed(2)}%</td>
                            <td>${new Date(trade.timestamp).toLocaleString()}</td>
                        </tr>`;
                    }
                });
                
                tableHTML += '</tbody></table>';
                tradesContent.innerHTML = tableHTML;
            } else {
                tradesContent.innerHTML = '<p style="text-align:center;padding:20px;color:#6b7280;">No trades executed during backtest period</p>';
            }
        }
        
        // Load current settings on page load
        async function loadCurrentSettings() {
            try {
                const response = await fetch('/api/settings');
                const settings = await response.json();
                
                document.getElementById('shortWindow').value = settings.short_window;
                document.getElementById('longWindow').value = settings.long_window;
                document.getElementById('volumeThreshold').value = settings.volume_threshold;
                document.getElementById('stopLossPct').value = settings.stop_loss_pct;
                document.getElementById('symbols').value = settings.symbols;
            } catch (error) {
                console.error('Error loading settings:', error);
            }
        }
        
        loadCurrentSettings();
    </script>
</body>
</html>
"""