"""
Enhanced Dashboard with Position Details Modal
"""

ENHANCED_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Dashboard - Enhanced</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #1a1a2e;
            min-height: 100vh;
        }
        
        .container { max-width: 1400px; margin: 0 auto; }
        
        /* Header - same as before */
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
            color: #1a1a2e;
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
            text-decoration: none;
            cursor: pointer;
        }
        
        /* Main content */
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px 40px;
        }
        
        /* Positions table with clickable rows */
        .positions-table {
            width: 100%;
            background: white;
            border-radius: 12px;
            overflow: hidden;
        }
        
        .positions-table thead {
            background: #f8f9fa;
        }
        
        .positions-table th {
            padding: 16px;
            text-align: left;
            font-weight: 600;
            color: #666;
        }
        
        .positions-table td {
            padding: 16px;
            border-top: 1px solid #e9ecef;
        }
        
        .position-row {
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .position-row:hover {
            background-color: #f8f9fa;
        }
        
        .clickable-hint {
            font-size: 12px;
            color: #999;
            margin-top: 8px;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            overflow-y: auto;
        }
        
        .modal-content {
            background-color: white;
            margin: 40px auto;
            padding: 0;
            width: 90%;
            max-width: 1200px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        .modal-header {
            padding: 24px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 16px 16px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-header h2 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .close-modal {
            color: white;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            border: none;
            background: none;
        }
        
        .close-modal:hover {
            opacity: 0.8;
        }
        
        .modal-body {
            padding: 32px;
        }
        
        /* Position details sections */
        .details-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .detail-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }
        
        .detail-card h3 {
            font-size: 16px;
            font-weight: 600;
            color: #666;
            margin-bottom: 12px;
        }
        
        .detail-value {
            font-size: 24px;
            font-weight: 700;
            color: #1a1a2e;
        }
        
        .detail-subvalue {
            font-size: 14px;
            color: #999;
            margin-top: 4px;
        }
        
        .chart-container {
            background: white;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 32px;
            border: 1px solid #e9ecef;
        }
        
        .chart-container h3 {
            margin-bottom: 16px;
            font-size: 18px;
            font-weight: 600;
        }
        
        /* Scenarios section */
        .scenarios-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }
        
        .scenario-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        
        .scenario-card.best { border-top: 4px solid #10b981; }
        .scenario-card.worst { border-top: 4px solid #ef4444; }
        .scenario-card.day-end { border-top: 4px solid #3b82f6; }
        
        .scenario-title {
            font-size: 14px;
            font-weight: 600;
            color: #666;
            margin-bottom: 8px;
        }
        
        .scenario-price {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        
        .scenario-pnl {
            font-size: 16px;
            font-weight: 600;
        }
        
        /* Ratings table */
        .ratings-table {
            width: 100%;
            margin-bottom: 32px;
        }
        
        .ratings-table th {
            padding: 12px;
            background: #f8f9fa;
            text-align: left;
            font-weight: 600;
            color: #666;
        }
        
        .ratings-table td {
            padding: 12px;
            border-top: 1px solid #e9ecef;
        }
        
        .rating-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .rating-strong-bull { background: #10b981; color: white; }
        .rating-bull { background: #34d399; color: white; }
        .rating-soft-bull { background: #6ee7b7; color: #065f46; }
        .rating-neutral { background: #9ca3af; color: white; }
        .rating-soft-bear { background: #fca5a5; color: #991b1b; }
        .rating-bear { background: #f87171; color: white; }
        .rating-strong-bear { background: #ef4444; color: white; }
        
        /* Confidence meters */
        .confidence-section {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .confidence-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
        }
        
        .confidence-meter {
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 12px;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }
        
        /* Day end options */
        .options-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
        }
        
        .option-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            border: 2px solid #e9ecef;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .option-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        
        .option-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .option-risk {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .option-risk.low { background: #d1fae5; color: #065f46; }
        .option-risk.medium { background: #fef3c7; color: #92400e; }
        .option-risk.high { background: #fee2e2; color: #991b1b; }
        
        /* Entry logic section */
        .entry-logic {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 32px;
        }
        
        .entry-logic h3 {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .logic-item {
            margin-bottom: 12px;
            padding: 12px;
            background: white;
            border-radius: 8px;
        }
        
        .logic-label {
            font-size: 12px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        
        .logic-value {
            font-size: 14px;
            color: #1a1a2e;
        }
        
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo-section">
                <h1>Trading Dashboard</h1>
            </div>
            <div class="header-actions">
                <a href="/backtest" class="settings-btn">📊 Backtest</a>
                <a href="/settings" class="settings-btn">⚙️ Settings</a>
            </div>
        </div>
    </div>
    
    <div class="main-content">
        <h2 style="color: white; margin-bottom: 24px;">Open Positions</h2>
        <p class="clickable-hint" style="color: rgba(255,255,255,0.8);">💡 Click on any position to see detailed analysis</p>
        
        <div style="background: white; border-radius: 12px; overflow: hidden; margin-top: 16px;">
            <table class="positions-table" id="positionsTable">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Shares</th>
                        <th>Entry Price</th>
                        <th>Current Price</th>
                        <th>P&L</th>
                        <th>P&L %</th>
                    </tr>
                </thead>
                <tbody id="positionsBody">
                    <tr>
                        <td colspan="6" style="text-align: center; padding: 40px; color: #999;">
                            Loading positions...
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Position Details Modal -->
    <div id="positionModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalSymbol">AAPL - Position Details</h2>
                <button class="close-modal" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody">
                <p style="text-align: center; color: #999;">Loading...</p>
            </div>
        </div>
    </div>
    
    <script>
        let currentPositions = [];
        
        // Fetch positions
        async function fetchPositions() {
            try {
                const response = await fetch('/positions');
                const data = await response.json();
                currentPositions = data.positions || [];
                renderPositions();
            } catch (error) {
                console.error('Error fetching positions:', error);
            }
        }
        
        // Render positions table
        function renderPositions() {
            const tbody = document.getElementById('positionsBody');
            
            if (currentPositions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: #999;">No open positions</td></tr>';
                return;
            }
            
            tbody.innerHTML = currentPositions.map(pos => `
                <tr class="position-row" onclick="showPositionDetails('${pos.symbol}')">
                    <td style="font-weight: 600;">${pos.symbol}</td>
                    <td>${pos.shares.toFixed(2)}</td>
                    <td>$${pos.entry_price.toFixed(2)}</td>
                    <td>$${pos.current_price.toFixed(2)}</td>
                    <td class="${pos.pnl >= 0 ? 'positive' : 'negative'}">$${pos.pnl.toFixed(2)}</td>
                    <td class="${pos.pnl_pct >= 0 ? 'positive' : 'negative'}">${pos.pnl_pct.toFixed(2)}%</td>
                </tr>
            `).join('');
        }
        
        // Show position details
        async function showPositionDetails(symbol) {
            const modal = document.getElementById('positionModal');
            const modalBody = document.getElementById('modalBody');
            const modalSymbol = document.getElementById('modalSymbol');
            
            modalSymbol.textContent = `${symbol} - Position Details`;
            modalBody.innerHTML = '<p style="text-align: center; color: #999; padding: 40px;">Loading detailed analysis...</p>';
            modal.style.display = 'block';
            
            try {
                const response = await fetch(`/api/position-details/${symbol}`);
                const data = await response.json();
                
                renderPositionDetails(data);
            } catch (error) {
                console.error('Error fetching position details:', error);
                modalBody.innerHTML = '<p style="text-align: center; color: #ef4444; padding: 40px;">Error loading details</p>';
            }
        }
        
        // Render full position details
        function renderPositionDetails(data) {
            const modalBody = document.getElementById('modalBody');
            const state = data.current_state;
            const scenarios = data.scenarios;
            const ratings = data.historical_ratings;
            const confidences = data.confidences;
            const options = data.day_end_options;
            const entry = data.entry_logic;
            
            modalBody.innerHTML = `
                <!-- Current State -->
                <div class="details-grid">
                    <div class="detail-card">
                        <h3>Position Value</h3>
                        <div class="detail-value">$${state.position_value.toFixed(2)}</div>
                        <div class="detail-subvalue">${state.shares.toFixed(2)} shares</div>
                    </div>
                    <div class="detail-card">
                        <h3>Current P&L</h3>
                        <div class="detail-value ${state.current_pnl >= 0 ? 'positive' : 'negative'}">
                            $${state.current_pnl.toFixed(2)}
                        </div>
                        <div class="detail-subvalue">${state.current_pnl_pct.toFixed(2)}%</div>
                    </div>
                    <div class="detail-card">
                        <h3>Entry Price</h3>
                        <div class="detail-value">$${state.entry_price.toFixed(2)}</div>
                        <div class="detail-subvalue">Current: $${state.current_price.toFixed(2)}</div>
                    </div>
                </div>
                
                <!-- Live Chart -->
                <div class="chart-container">
                    <h3>📈 Live Price Chart (Today)</h3>
                    <canvas id="priceChart" height="80"></canvas>
                </div>
                
                <!-- Entry Logic -->
                <div class="entry-logic">
                    <h3>🎯 Entry Logic & Reasoning</h3>
                    <div class="logic-item">
                        <div class="logic-label">Screening Model</div>
                        <div class="logic-value">${data.models_used.screening}</div>
                    </div>
                    <div class="logic-item">
                        <div class="logic-label">Screening Logic</div>
                        <div class="logic-value">${entry.screening_logic}</div>
                    </div>
                    <div class="logic-item">
                        <div class="logic-label">Day Trading Model</div>
                        <div class="logic-value">${data.models_used.daytrade}</div>
                    </div>
                    <div class="logic-item">
                        <div class="logic-label">Entry Signal</div>
                        <div class="logic-value">${entry.entry_signal}</div>
                    </div>
                    <div class="logic-item">
                        <div class="logic-label">Entry Time</div>
                        <div class="logic-value">${new Date(state.entry_time).toLocaleString()}</div>
                    </div>
                </div>
                
                <!-- Scenarios -->
                <h3 style="margin-bottom: 16px;">📊 Price Scenarios</h3>
                <div class="scenarios-grid">
                    <div class="scenario-card best">
                        <div class="scenario-title">Best Case</div>
                        <div class="scenario-price positive">$${scenarios.best_case.target_price.toFixed(2)}</div>
                        <div class="scenario-pnl positive">+$${scenarios.best_case.potential_pnl.toFixed(2)}</div>
                        <div class="detail-subvalue">${scenarios.best_case.description}</div>
                    </div>
                    <div class="scenario-card day-end">
                        <div class="scenario-title">Day End Target</div>
                        <div class="scenario-price">$${scenarios.day_end.target_price.toFixed(2)}</div>
                        <div class="scenario-pnl">+$${scenarios.day_end.potential_pnl.toFixed(2)}</div>
                        <div class="detail-subvalue">${scenarios.day_end.description}</div>
                    </div>
                    <div class="scenario-card worst">
                        <div class="scenario-title">Worst Case</div>
                        <div class="scenario-price negative">$${scenarios.worst_case.target_price.toFixed(2)}</div>
                        <div class="scenario-pnl negative">$${scenarios.worst_case.potential_pnl.toFixed(2)}</div>
                        <div class="detail-subvalue">${scenarios.worst_case.description}</div>
                    </div>
                </div>
                
                <!-- Confidence Scores -->
                <h3 style="margin-bottom: 16px;">🎯 Trading Confidence</h3>
                <div class="confidence-section">
                    <div class="confidence-card">
                        <h4>Day Trade Confidence</h4>
                        <div style="font-size: 24px; font-weight: 700; margin: 8px 0;">${confidences.day_trade.score}/100</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">${confidences.day_trade.level}</div>
                        <div class="confidence-meter">
                            <div class="confidence-fill" style="width: ${confidences.day_trade.score}%"></div>
                        </div>
                        <div style="font-size: 12px; color: #999; margin-top: 8px;">${confidences.day_trade.factors || ''}</div>
                    </div>
                    <div class="confidence-card">
                        <h4>Long Term Confidence</h4>
                        <div style="font-size: 24px; font-weight: 700; margin: 8px 0;">${confidences.long_term.score}/100</div>
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">${confidences.long_term.level}</div>
                        <div class="confidence-meter">
                            <div class="confidence-fill" style="width: ${confidences.long_term.score}%"></div>
                        </div>
                        <div style="font-size: 12px; color: #999; margin-top: 8px;">${confidences.long_term.factors || ''}</div>
                    </div>
                </div>
                
                <!-- Historical Ratings -->
                <h3 style="margin-bottom: 16px;">📅 Historical Performance Ratings</h3>
                <table class="ratings-table">
                    <thead>
                        <tr>
                            <th>Time Period</th>
                            <th>Rating</th>
                            <th>Change</th>
                            <th>Trend Strength</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(ratings).map(([period, rating]) => `
                            <tr>
                                <td>${period.replace('_', ' ').toUpperCase()}</td>
                                <td><span class="rating-badge rating-${rating.rating.toLowerCase().replace(' ', '-')}">${rating.rating}</span></td>
                                <td class="${rating.change_pct >= 0 ? 'positive' : 'negative'}">${rating.change_pct >= 0 ? '+' : ''}${rating.change_pct.toFixed(2)}%</td>
                                <td>${rating.trend_strength ? rating.trend_strength.toFixed(1) + '%' : 'N/A'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                
                <!-- Day End Options -->
                <h3 style="margin-bottom: 16px;">⏰ Day End Closeout Options</h3>
                <div class="options-grid">
                    ${options.map(option => `
                        <div class="option-card">
                            <div class="option-title">${option.action}</div>
                            <span class="option-risk ${option.risk.toLowerCase()}">${option.risk} Risk</span>
                            <p style="font-size: 14px; color: #666; margin: 12px 0;">${option.description}</p>
                            <p style="font-size: 12px; color: #999;">${option.risk_description}</p>
                        </div>
                    `).join('')}
                </div>
            `;
            
            // Load chart data and render
            loadPriceChart(data.symbol);
        }
        
        // Load and render price chart
        async function loadPriceChart(symbol) {
            try {
                const response = await fetch(`/api/live-chart/${symbol}`);
                const chartData = await response.json();
                
                if (chartData.error) {
                    console.error('Chart error:', chartData.error);
                    return;
                }
                
                const ctx = document.getElementById('priceChart');
                if (!ctx) return;
                
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: chartData.data.map(d => new Date(d.time).toLocaleTimeString()),
                        datasets: [{
                            label: 'Price',
                            data: chartData.data.map(d => d.close),
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                ticks: {
                                    callback: (value) => '$' + value.toFixed(2)
                                }
                            }
                        }
                    }
                });
            } catch (error) {
                console.error('Error loading chart:', error);
            }
        }
        
        // Close modal
        function closeModal() {
            document.getElementById('positionModal').style.display = 'none';
        }
        
        // Close modal on outside click
        window.onclick = function(event) {
            const modal = document.getElementById('positionModal');
            if (event.target === modal) {
                closeModal();
            }
        }
        
        // Initial load
        fetchPositions();
        
        // Refresh every 10 seconds
        setInterval(fetchPositions, 10000);
    </script>
</body>
</html>
"""