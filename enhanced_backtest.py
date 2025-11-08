"""
Enhanced Backtest Page with Real-Time SSE Progress Tracking
Complete HTML page with Server-Sent Events for live updates

UPDATED: Added daily allocation percentage and settlement tracking controls
"""

ENHANCED_BACKTEST_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Backtest - Trading Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Header */
        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        h1 {
            color: #667eea;
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .back-link {
            display: inline-block;
            margin-bottom: 15px;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        
        .back-link:hover {
            text-decoration: underline;
        }
        
        /* Cards */
        .card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        h2 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #333;
        }
        
        /* Form Elements */
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #555;
        }
        
        select, input[type="number"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        small {
            display: block;
            margin-top: 4px;
            color: #666;
            font-size: 12px;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            width: 100%;
        }
        
        .button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Allocation Preview Box */
        .allocation-preview {
            background: linear-gradient(135deg, #f0f7ff 0%, #e6f2ff 100%);
            padding: 20px;
            border-radius: 12px;
            border: 2px solid #667eea;
            margin-bottom: 20px;
        }
        
        .allocation-preview h3 {
            color: #667eea;
            font-size: 18px;
            margin: 0 0 12px 0;
        }
        
        .allocation-preview p {
            margin: 8px 0;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .allocation-preview .highlight {
            font-size: 20px;
            font-weight: 700;
            color: #667eea;
            margin-top: 12px;
        }
        
        /* Progress Section */
        .progress-section {
            display: none;
        }
        
        .progress-section.active {
            display: block;
        }
        
        .progress-bar-container {
            background: #f0f0f0;
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        
        .progress-bar {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }
        
        .status-message {
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 5px;
            font-size: 14px;
            margin-bottom: 15px;
        }
        
        .status-log {
            max-height: 300px;
            overflow-y: auto;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.6;
        }
        
        .status-log div {
            padding: 4px 0;
            border-bottom: 1px solid #e9ecef;
        }
        
        .status-log div:last-child {
            border-bottom: none;
        }
        
        .status-log .info {
            color: #0066cc;
        }
        
        .status-log .detail {
            color: #6c757d;
            font-size: 11px;
            padding-left: 20px;
            border-left: 2px solid #e9ecef;
            margin-left: 10px;
            margin-top: 2px;
        }
        
        .status-log .success {
            color: #28a745;
            font-weight: 600;
        }
        
        .status-log .error {
            color: #dc3545;
            font-weight: 600;
        }
        
        /* Results Section */
        .results-section {
            display: none;
        }
        
        .results-section.active {
            display: block;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .metric-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: #333;
        }
        
        .metric-value.positive {
            color: #28a745;
        }
        
        .metric-value.negative {
            color: #dc3545;
        }
        
        .publish-button {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 20px;
        }
        
        .publish-button:hover:not(:disabled) {
            box-shadow: 0 5px 20px rgba(17, 153, 142, 0.4);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>🧪 Comprehensive Backtest</h1>
            <p>Test strategies with historical data before going live</p>
        </header>
        
        <!-- Configuration Form -->
        <div class="card">
            <h2>Backtest Configuration</h2>
            
            <div class="grid-2">
                <div class="form-group">
                    <label for="screenerModel">Screening Model</label>
                    <select id="screenerModel">
                        <option value="gap_volatility">Gap & Volatility</option>
                        <option value="technical_momentum">Technical Momentum</option>
                        <option value="trend_strength">Trend Strength</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="dayModel">Day Trading Model</label>
                    <select id="dayModel">
                        <option value="ma_crossover">MA Crossover</option>
                        <option value="vwap_mean_reversion">VWAP Mean Reversion</option>
                        <option value="momentum_breakout">Momentum Breakout</option>
                    </select>
                </div>
            </div>
            
            <div class="grid-2">
                <div class="form-group">
                    <label for="topN">Top N Stocks per Day</label>
                    <input type="number" id="topN" value="3" min="1" max="10">
                </div>
                
                <div class="form-group">
                    <label for="minScore">Minimum Score</label>
                    <input type="number" id="minScore" value="60" min="0" max="100">
                </div>
            </div>
            
            <div class="grid-2">
                <div class="form-group">
                    <label for="days">Days to Test</label>
                    <input type="number" id="days" value="30" min="1" max="90">
                </div>
                
                <div class="form-group">
                    <label for="initialCapital">Initial Capital ($)</label>
                    <input type="number" id="initialCapital" value="10000" min="100" step="100">
                </div>
            </div>
            
            <!-- NEW: Daily Allocation Controls -->
            <div class="grid-2">
                <div class="form-group">
                    <label for="dailyAllocation">Daily Allocation %</label>
                    <input type="number" id="dailyAllocation" value="10" min="1" max="100" step="1">
                    <small>Percentage of buying power to use per day</small>
                </div>
                
                <div class="form-group">
                    <label for="settlementDays">Settlement Period (days)</label>
                    <input type="number" id="settlementDays" value="2" min="0" max="5" step="1">
                    <small>T+2 settlement (0 = instant for testing)</small>
                </div>
            </div>
            
            <!-- NEW: Allocation Preview -->
            <div class="allocation-preview">
                <h3>📊 Allocation Preview</h3>
                <p>
                    With <strong>$<span id="previewCapital">10,000</span></strong> 
                    and <strong><span id="previewAllocation">10</span>%</strong> daily allocation,
                    split among <strong><span id="previewTopN">3</span></strong> stocks:
                </p>
                <p class="highlight">
                    Per Stock: $<span id="previewPerStock">333.33</span>
                </p>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="forceExecution">
                    Force execution even if confidence is low
                </label>
            </div>
            
            <button class="button" id="runBacktest">Run Backtest</button>
        </div>
        
        <!-- Progress Section -->
        <div class="card progress-section" id="progressSection">
            <h2>⏳ Backtest in Progress</h2>
            
            <div class="progress-bar-container">
                <div class="progress-bar" id="progressBar">0%</div>
            </div>
            
            <div class="status-message" id="statusMessage">
                Initializing...
            </div>
            
            <h3 style="margin-top: 20px; margin-bottom: 10px;">Activity Log</h3>
            <div class="status-log" id="statusLog"></div>
        </div>
        
        <!-- Results Section -->
        <div class="card results-section" id="resultsSection">
            <h2>📊 Backtest Results</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Initial Capital</div>
                    <div class="metric-value" id="initialCapitalResult">$0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Final Value</div>
                    <div class="metric-value" id="finalValue">$0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Return</div>
                    <div class="metric-value" id="totalReturn">0%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value" id="winRate">0%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value" id="totalTrades">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Winning Trades</div>
                    <div class="metric-value positive" id="winningTrades">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Losing Trades</div>
                    <div class="metric-value negative" id="losingTrades">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value" id="profitFactor">0</div>
                </div>
            </div>
            
            <div class="grid-2">
                <div>
                    <h3 style="margin-bottom: 10px;">Strategy Info</h3>
                    <p><strong>Strategy:</strong> <span id="strategy">-</span></p>
                    <p><strong>Unique Stocks:</strong> <span id="uniqueStocks">-</span></p>
                    <p><strong>Avg Win:</strong> <span id="avgWin">-</span></p>
                    <p><strong>Avg Loss:</strong> <span id="avgLoss">-</span></p>
                </div>
            </div>
            
            <button class="publish-button" id="publishButton">
                🚀 Publish to Live Trading
            </button>
        </div>
    </div>
    
    <script>
        let currentBacktestResults = null;
        
        // Update allocation preview in real-time
        function updateAllocationPreview() {
            const capital = parseFloat(document.getElementById('initialCapital').value) || 10000;
            const pct = parseFloat(document.getElementById('dailyAllocation').value) || 10;
            const topN = parseInt(document.getElementById('topN').value) || 3;
            
            const dailyTotal = capital * (pct / 100);
            const perStock = dailyTotal / topN;
            
            document.getElementById('previewCapital').textContent = capital.toLocaleString();
            document.getElementById('previewAllocation').textContent = pct.toFixed(0);
            document.getElementById('previewTopN').textContent = topN;
            document.getElementById('previewPerStock').textContent = perStock.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
        
        // Attach event listeners for live preview updates
        document.getElementById('initialCapital').addEventListener('input', updateAllocationPreview);
        document.getElementById('dailyAllocation').addEventListener('input', updateAllocationPreview);
        document.getElementById('topN').addEventListener('input', updateAllocationPreview);
        
        // Initial calculation
        updateAllocationPreview();
        
        // Helper Functions
        function addLog(message, className = 'info') {
            const logDiv = document.getElementById('statusLog');
            const entry = document.createElement('div');
            entry.className = className;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            logDiv.appendChild(entry);
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        function updateProgress(percent, message) {
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = `${percent}%`;
            progressBar.textContent = `${percent}%`;
            document.getElementById('statusMessage').textContent = message;
        }
        
        function displayResults(data) {
            document.getElementById('initialCapitalResult').textContent = `$${data.initial_capital.toLocaleString()}`;
            document.getElementById('finalValue').textContent = `$${data.final_value.toLocaleString()}`;
            
            const returnElement = document.getElementById('totalReturn');
            returnElement.textContent = `${data.total_return_pct > 0 ? '+' : ''}${data.total_return_pct.toFixed(2)}%`;
            returnElement.className = 'metric-value ' + (data.total_return_pct >= 0 ? 'positive' : 'negative');
            
            document.getElementById('winRate').textContent = `${data.win_rate.toFixed(1)}%`;
            document.getElementById('totalTrades').textContent = data.total_trades;
            document.getElementById('winningTrades').textContent = data.winning_trades;
            document.getElementById('losingTrades').textContent = data.losing_trades;
            document.getElementById('profitFactor').textContent = data.profit_factor.toFixed(2);
            document.getElementById('strategy').textContent = data.strategy;
            document.getElementById('uniqueStocks').textContent = data.unique_stocks_traded;
            document.getElementById('avgWin').textContent = `$${Math.abs(data.avg_win).toFixed(2)}`;
            document.getElementById('avgLoss').textContent = `$${Math.abs(data.avg_loss).toFixed(2)}`;
            
            addLog('✅ Backtest complete!', 'success');
        }
        
        // Run Backtest Button Handler
        document.getElementById('runBacktest').addEventListener('click', async () => {
            const screenerModel = document.getElementById('screenerModel').value;
            const dayModel = document.getElementById('dayModel').value;
            const topN = parseInt(document.getElementById('topN').value);
            const minScore = parseFloat(document.getElementById('minScore').value);
            const days = parseInt(document.getElementById('days').value);
            const initialCapital = parseFloat(document.getElementById('initialCapital').value);
            const forceExecution = document.getElementById('forceExecution').checked;
            
            // NEW: Get allocation parameters
            const dailyAllocation = parseFloat(document.getElementById('dailyAllocation').value) / 100;
            const settlementDays = parseInt(document.getElementById('settlementDays').value);
            
            // Reset UI
            document.getElementById('statusLog').innerHTML = '';
            document.getElementById('progressSection').classList.add('active');
            document.getElementById('resultsSection').classList.remove('active');
            document.getElementById('runBacktest').disabled = true;
            
            updateProgress(0, 'Initializing...');
            addLog('Starting backtest...', 'info');
            
            // Build URL with NEW parameters
            const url = `/api/comprehensive-backtest-stream?` +
                `screener_model=${screenerModel}` +
                `&day_model=${dayModel}` +
                `&top_n_stocks=${topN}` +
                `&min_score=${minScore}` +
                `&days=${days}` +
                `&initial_capital=${initialCapital}` +
                `&force_execution=${forceExecution}` +
                `&daily_allocation=${dailyAllocation}` +
                `&settlement_days=${settlementDays}`;
            
            try {
                const eventSource = new EventSource(url);
                
                eventSource.addEventListener('message', (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.type === 'progress') {
                            updateProgress(data.percent, data.message);
                            addLog(data.message, 'info');
                            if (data.detail) {
                                addLog(`  → ${data.detail}`, 'detail');
                            }
                        } else if (data.type === 'complete') {
                            updateProgress(100, 'Backtest complete!');
                            displayResults(data.results);
                            currentBacktestResults = data.results;
                            document.getElementById('resultsSection').classList.add('active');
                            document.getElementById('runBacktest').disabled = false;
                            eventSource.close();
                        } else if (data.type === 'error') {
                            addLog(`❌ Error: ${data.message}`, 'error');
                            alert(`Backtest failed: ${data.message}`);
                            document.getElementById('runBacktest').disabled = false;
                            eventSource.close();
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e);
                    }
                });
                
                eventSource.addEventListener('error', (event) => {
                    console.error('SSE error:', event);
                    addLog('❌ Connection error', 'error');
                    document.getElementById('runBacktest').disabled = false;
                    eventSource.close();
                });
                
            } catch (error) {
                console.error('Error starting backtest:', error);
                addLog(`❌ Error: ${error.message}`, 'error');
                document.getElementById('runBacktest').disabled = false;
            }
        });
        
        // Publish to Live Trading
        document.getElementById('publishButton').addEventListener('click', async () => {
            if (!currentBacktestResults) {
                alert('No backtest results to publish');
                return;
            }
            
            if (!confirm('Publish this configuration to live trading?')) {
                return;
            }
            
            try {
                const screenerModel = document.getElementById('screenerModel').value;
                const dayModel = document.getElementById('dayModel').value;
                const topN = parseInt(document.getElementById('topN').value);
                const minScore = parseFloat(document.getElementById('minScore').value);
                const forceExecution = document.getElementById('forceExecution').checked;
                
                const response = await fetch('/api/publish-backtest', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        screener_model: screenerModel,
                        screener_params: {},
                        day_model: dayModel,
                        day_model_params: {},
                        top_n_stocks: topN,
                        min_score: minScore,
                        force_execution: forceExecution
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    alert('✅ Configuration published to live trading!');
                } else {
                    alert('❌ Failed to publish: ' + result.message);
                }
                
            } catch (error) {
                console.error('Publish error:', error);
                alert('❌ Failed to publish: ' + error.message);
            }
        });
    </script>
</body>
</html>
"""