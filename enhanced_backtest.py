"""
Enhanced Backtest Page with Real-Time SSE Progress Tracking
Complete HTML page with Server-Sent Events for live updates
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
        
        .status-log .warning {
            color: #ffc107;
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
                    <input type="number" id="initialCapital" value="10000" min="1000" step="1000">
                </div>
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
            </div>
            
            <div class="metrics-grid">
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
                    <div class="metric-value" id="profitFactor">0.00</div>
                </div>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Strategy</div>
                    <div class="metric-value" style="font-size: 18px;" id="strategy">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Unique Stocks</div>
                    <div class="metric-value" id="uniqueStocks">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Win</div>
                    <div class="metric-value positive" id="avgWin">$0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Loss</div>
                    <div class="metric-value negative" id="avgLoss">$0</div>
                </div>
            </div>
            
            <button class="button publish-button" id="publishButton">
                ✅ Publish to Live Trading
            </button>
        </div>
    </div>
    
    <script>
        const runButton = document.getElementById('runBacktest');
        const publishButton = document.getElementById('publishButton');
        const progressSection = document.getElementById('progressSection');
        const resultsSection = document.getElementById('resultsSection');
        const progressBar = document.getElementById('progressBar');
        const statusMessage = document.getElementById('statusMessage');
        const statusLog = document.getElementById('statusLog');
        
        let logEntries = [];
        let currentEventSource = null;
        let lastBacktestConfig = null;
        
        function addLog(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            const entry = `[${timestamp}] ${message}`;
            logEntries.push({ message: entry, type });
            
            // Keep last 100 entries
            if (logEntries.length > 100) {
                logEntries.shift();
            }
            
            // Update log display
            statusLog.innerHTML = logEntries
                .map(e => `<div class="${e.type}">${e.message}</div>`)
                .join('');
            statusLog.scrollTop = statusLog.scrollHeight;
        }
        
        function updateProgress(percent, message) {
            progressBar.style.width = `${percent}%`;
            progressBar.textContent = `${percent}%`;
            statusMessage.textContent = message;
            addLog(message, 'info');
        }
        
        function showResults(data) {
            // Hide progress, show results
            progressSection.classList.remove('active');
            resultsSection.classList.add('active');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
            
            // Update metrics
            document.getElementById('initialCapitalResult').textContent = 
                `$${data.initial_capital.toLocaleString()}`;
            document.getElementById('finalValue').textContent = 
                `$${data.final_value.toLocaleString()}`;
            
            const returnValue = document.getElementById('totalReturn');
            returnValue.textContent = `${data.total_return_pct.toFixed(2)}%`;
            returnValue.className = 'metric-value ' + 
                (data.total_return_pct >= 0 ? 'positive' : 'negative');
            
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
        
        // Main backtest execution with SSE
        runButton.addEventListener('click', async () => {
            // Disable button
            runButton.disabled = true;
            runButton.textContent = 'Running...';
            
            // Reset and show progress
            logEntries = [];
            progressSection.classList.add('active');
            resultsSection.classList.remove('active');
            updateProgress(0, 'Connecting to backtest stream...');
            
            // Gather parameters
            const params = {
                screener_model: document.getElementById('screenerModel').value,
                screener_params: {},
                day_model: document.getElementById('dayModel').value,
                day_model_params: {},
                top_n_stocks: parseInt(document.getElementById('topN').value),
                min_score: parseFloat(document.getElementById('minScore').value),
                force_execution: document.getElementById('forceExecution').checked,
                days: parseInt(document.getElementById('days').value),
                initial_capital: parseFloat(document.getElementById('initialCapital').value)
            };
            
            // Store config for publishing later
            lastBacktestConfig = params;
            
            try {
                addLog('Establishing SSE connection...', 'info');
                
                // Build query string
                const queryParams = new URLSearchParams({
                    screener_model: params.screener_model,
                    day_model: params.day_model,
                    top_n_stocks: params.top_n_stocks,
                    min_score: params.min_score,
                    days: params.days,
                    initial_capital: params.initial_capital,
                    force_execution: params.force_execution
                });
                
                // Create EventSource for Server-Sent Events
                currentEventSource = new EventSource(`/api/comprehensive-backtest-stream?${queryParams}`);
                
                currentEventSource.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.type === 'progress') {
                            // Update progress bar and main message
                            updateProgress(data.percent, data.message);
                            
                            // Add detailed info to log
                            if (data.detail) {
                                addLog(data.detail, 'detail');
                            }
                            
                        } else if (data.type === 'complete') {
                            // Backtest finished successfully
                            updateProgress(100, 'Backtest complete!');
                            addLog('✅ Backtest completed successfully', 'success');
                            
                            // Close connection
                            currentEventSource.close();
                            currentEventSource = null;
                            
                            // Show results
                            if (data.results) {
                                showResults(data.results);
                            }
                            
                            // Re-enable button
                            runButton.disabled = false;
                            runButton.textContent = 'Run Backtest';
                            
                        } else if (data.type === 'error') {
                            // Error occurred
                            addLog(`❌ Error: ${data.message}`, 'error');
                            statusMessage.textContent = `Error: ${data.message}`;
                            statusMessage.style.background = '#fee2e2';
                            statusMessage.style.borderColor = '#dc3545';
                            
                            // Close connection
                            if (currentEventSource) {
                                currentEventSource.close();
                                currentEventSource = null;
                            }
                            
                            // Re-enable button
                            runButton.disabled = false;
                            runButton.textContent = 'Run Backtest';
                            
                            alert(`Backtest failed: ${data.message}`);
                        }
                        
                    } catch (parseError) {
                        console.error('Error parsing SSE data:', parseError);
                        addLog(`Parse error: ${parseError.message}`, 'error');
                    }
                };
                
                currentEventSource.onerror = (error) => {
                    console.error('SSE connection error:', error);
                    addLog('⚠️ Connection error. Reconnecting...', 'warning');
                    
                    // SSE will auto-reconnect, but if it fails completely, clean up
                    setTimeout(() => {
                        if (currentEventSource && currentEventSource.readyState === EventSource.CLOSED) {
                            addLog('❌ Connection failed. Please try again.', 'error');
                            runButton.disabled = false;
                            runButton.textContent = 'Run Backtest';
                            currentEventSource = null;
                        }
                    }, 5000);
                };
                
            } catch (error) {
                console.error('Error starting backtest:', error);
                addLog(`Error: ${error.message}`, 'error');
                statusMessage.textContent = `Error: ${error.message}`;
                statusMessage.style.background = '#fee2e2';
                statusMessage.style.borderColor = '#dc3545';
                alert(`Backtest failed: ${error.message}`);
                
                runButton.disabled = false;
                runButton.textContent = 'Run Backtest';
            }
        });
        
        // Publish to live trading
        publishButton.addEventListener('click', async () => {
            if (!confirm('Publish this backtest configuration to live trading?')) {
                return;
            }
            
            publishButton.disabled = true;
            publishButton.textContent = 'Publishing...';
            
            try {
                const response = await fetch('/api/publish-backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(lastBacktestConfig)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                alert('✅ Configuration published to live trading!');
                
            } catch (error) {
                alert(`Failed to publish: ${error.message}`);
            } finally {
                publishButton.disabled = false;
                publishButton.textContent = '✅ Publish to Live Trading';
            }
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (currentEventSource) {
                currentEventSource.close();
            }
        });
    </script>
</body>
</html>
"""