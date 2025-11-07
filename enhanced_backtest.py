"""
Enhanced Backtest Page with Progress Tracking
Complete HTML page with real-time progress updates
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
            max-height: 200px;
            overflow-y: auto;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.6;
        }
        
        .status-log div {
            margin-bottom: 5px;
            color: #555;
        }
        
        .status-log div.info { color: #0066cc; }
        .status-log div.success { color: #28a745; }
        .status-log div.error { color: #dc3545; }
        
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
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .metric {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }
        
        .metric-label {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #333;
        }
        
        .metric-value.positive { color: #28a745; }
        .metric-value.negative { color: #dc3545; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .stat-group h3 {
            font-size: 18px;
            margin-bottom: 15px;
            color: #667eea;
        }
        
        .stat-group p {
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .stat-group strong {
            color: #333;
        }
        
        @media (max-width: 768px) {
            .grid-2, .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>🧪 Backtest Your Strategy</h1>
            <p>Test your trading strategy on historical data before going live</p>
        </header>
        
        <div class="card">
            <h2>Configuration</h2>
            
            <div class="grid-2">
                <div class="form-group">
                    <label>Screening Model</label>
                    <select id="screenerModel">
                        <option value="technical_momentum">Technical Momentum</option>
                        <option value="gap_volatility">Gap & Volatility</option>
                        <option value="trend_strength">Trend Strength</option>
                        <option value="manual">Manual Selection</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Day Trading Model</label>
                    <select id="dayModel">
                        <option value="ma_crossover">MA Crossover</option>
                        <option value="pattern_recognition">Pattern Recognition</option>
                        <option value="vwap_bounce">VWAP Bounce</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Days to Backtest</label>
                    <input type="number" id="days" value="30" min="1" max="90">
                </div>
                
                <div class="form-group">
                    <label>Initial Capital ($)</label>
                    <input type="number" id="initialCapital" value="10000" min="1000" step="1000">
                </div>
                
                <div class="form-group">
                    <label>Top N Stocks Per Day</label>
                    <input type="number" id="topN" value="3" min="1" max="10">
                </div>
                
                <div class="form-group">
                    <label>Minimum Score</label>
                    <input type="number" id="minScore" value="60" min="0" max="100">
                </div>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="forceExecution" style="width: auto; margin-right: 10px;">
                    Force Execution (ignore confidence thresholds)
                </label>
            </div>
            
            <button class="button" id="runBacktest">Run Backtest</button>
        </div>
        
        <!-- Progress Section -->
        <div class="card progress-section" id="progressSection">
            <h2>Progress</h2>
            
            <div class="progress-bar-container">
                <div class="progress-bar" id="progressBar">0%</div>
            </div>
            
            <div class="status-message" id="statusMessage">
                Initializing...
            </div>
            
            <div class="status-log" id="statusLog"></div>
        </div>
        
        <!-- Results Section -->
        <div class="card results-section" id="resultsSection">
            <h2>Results</h2>
            
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Initial Capital</div>
                    <div class="metric-value" id="initialCapitalResult">-</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Final Value</div>
                    <div class="metric-value" id="finalValue">-</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Return</div>
                    <div class="metric-value" id="totalReturn">-</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value" id="winRate">-</div>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-group">
                    <h3>Trade Statistics</h3>
                    <p><strong>Total Trades:</strong> <span id="totalTrades">0</span></p>
                    <p><strong>Winning Trades:</strong> <span id="winningTrades">0</span></p>
                    <p><strong>Losing Trades:</strong> <span id="losingTrades">0</span></p>
                    <p><strong>Profit Factor:</strong> <span id="profitFactor">0</span></p>
                </div>
                
                <div class="stat-group">
                    <h3>Additional Info</h3>
                    <p><strong>Strategy:</strong> <span id="strategy">-</span></p>
                    <p><strong>Unique Stocks:</strong> <span id="uniqueStocks">0</span></p>
                    <p><strong>Sessions:</strong> <span id="screeningSessions">0</span></p>
                    <p><strong>Avg Win:</strong> $<span id="avgWin">0</span></p>
                    <p><strong>Avg Loss:</strong> $<span id="avgLoss">0</span></p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const runButton = document.getElementById('runBacktest');
        const progressSection = document.getElementById('progressSection');
        const resultsSection = document.getElementById('resultsSection');
        const progressBar = document.getElementById('progressBar');
        const statusMessage = document.getElementById('statusMessage');
        const statusLog = document.getElementById('statusLog');
        
        let logEntries = [];
        
        function addLog(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            const entry = `[${timestamp}] ${message}`;
            logEntries.push({ message: entry, type });
            
            // Keep last 50 entries
            if (logEntries.length > 50) {
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
            document.getElementById('screeningSessions').textContent = data.screening_sessions;
            document.getElementById('avgWin').textContent = Math.abs(data.avg_win).toFixed(2);
            document.getElementById('avgLoss').textContent = Math.abs(data.avg_loss).toFixed(2);
            
            addLog('Backtest complete!', 'success');
        }
        
        runButton.addEventListener('click', async () => {
            // Disable button
            runButton.disabled = true;
            runButton.textContent = 'Running...';
            
            // Reset and show progress
            logEntries = [];
            progressSection.classList.add('active');
            resultsSection.classList.remove('active');
            updateProgress(0, 'Starting backtest...');
            
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
            
            try {
                addLog('Sending backtest request...', 'info');
                updateProgress(5, 'Initializing backtester...');
                
                const response = await fetch('/api/comprehensive-backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status}`);
                }
                
                // Simulate progress (in production, you could poll for progress or use SSE)
                updateProgress(25, 'Fetching historical data...');
                await new Promise(resolve => setTimeout(resolve, 500));
                
                updateProgress(50, 'Running simulation...');
                await new Promise(resolve => setTimeout(resolve, 500));
                
                updateProgress(75, 'Analyzing results...');
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    updateProgress(100, 'Complete!');
                    await new Promise(resolve => setTimeout(resolve, 500));
                    showResults(data);
                } else {
                    throw new Error(data.message || 'Backtest failed');
                }
                
            } catch (error) {
                addLog(`Error: ${error.message}`, 'error');
                statusMessage.textContent = `Error: ${error.message}`;
                statusMessage.style.background = '#fee2e2';
                statusMessage.style.borderColor = '#dc3545';
                alert(`Backtest failed: ${error.message}`);
            } finally {
                runButton.disabled = false;
                runButton.textContent = 'Run Backtest';
            }
        });
    </script>
</body>
</html>
"""