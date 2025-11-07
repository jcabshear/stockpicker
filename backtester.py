"""
Enhanced Backtest Page HTML
Replace BACKTEST_PAGE_HTML in dashboard.py with this
"""

ENHANCED_BACKTEST_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Backtest - Trading Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #1a1a2e;
            min-height: 100vh;
            padding: 0;
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 0; }
        
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
        
        h1 { font-size: 28px; font-weight: 700; color: #1a1a2e; }
        
        /* Main Content */
        .main-content { padding: 32px 40px; }
        
        .section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.06);
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f3f4f6;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .section-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            font-size: 16px;
            font-weight: 700;
        }
        
        .section-subtitle {
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 16px;
        }
        
        /* Model Cards */
        .model-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        
        .model-card {
            background: #f9fafb;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .model-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        
        .model-card.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        }
        
        .model-card input[type="radio"] {
            margin-right: 12px;
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        .model-name {
            font-size: 16px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 8px;
        }
        
        .model-description {
            font-size: 13px;
            color: #6b7280;
            line-height: 1.5;
        }
        
        .model-params {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
            display: none;
        }
        
        .model-card.selected .model-params {
            display: block;
        }
        
        /* Form Elements */
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }
        
        .form-group { margin-bottom: 0; }
        
        .form-label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 6px;
        }
        
        .form-input, .form-select {
            width: 100%;
            padding: 10px 14px;
            font-size: 14px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            transition: all 0.3s;
            font-family: inherit;
        }
        
        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px;
            background: #f9fafb;
            border-radius: 8px;
            cursor: pointer;
        }
        
        .checkbox-group:hover {
            background: #f3f4f6;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .checkbox-label {
            font-size: 14px;
            font-weight: 600;
            color: #374151;
            cursor: pointer;
        }
        
        /* Pattern Selector */
        .pattern-selector {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }
        
        .pattern-checkbox {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-size: 13px;
        }
        
        .pattern-checkbox input {
            width: 16px;
            height: 16px;
        }
        
        /* Buttons */
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
            transform: none;
        }
        
        /* Messages */
        .message {
            padding: 16px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
            font-weight: 600;
        }
        
        .message-loading {
            background: #dbeafe;
            color: #1e40af;
            display: block;
        }
        
        .message-error {
            background: #fee2e2;
            color: #991b1b;
            display: block;
        }
        
        /* Results */
        .results-section { display: none; }
        
        .results-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
            font-size: 11px;
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
        
        /* Daily Breakdown */
        .daily-breakdown {
            margin-top: 24px;
        }
        
        .day-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        
        .day-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f3f4f6;
        }
        
        .day-date {
            font-size: 16px;
            font-weight: 700;
            color: #1a1a2e;
        }
        
        .day-pnl {
            font-size: 18px;
            font-weight: 700;
        }
        
        .day-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }
        
        .day-stat {
            font-size: 13px;
            color: #6b7280;
        }
        
        .day-stat strong {
            color: #1a1a2e;
            font-weight: 600;
        }
        
        .symbol-list {
            margin-top: 12px;
            padding: 12px;
            background: #f9fafb;
            border-radius: 8px;
        }
        
        .symbol-badge {
            display: inline-block;
            padding: 4px 12px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        
        /* Trades Table */
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 16px;
        }
        
        thead {
            background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
        }
        
        th {
            text-align: left;
            padding: 12px;
            color: #6b7280;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            border-bottom: 2px solid #e5e7eb;
        }
        
        th:first-child { border-radius: 8px 0 0 0; }
        th:last-child { border-radius: 0 8px 0 0; }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #f3f4f6;
            font-size: 13px;
            color: #374151;
        }
        
        tbody tr:hover {
            background: #f9fafb;
        }
        
        .positive { color: #10b981; font-weight: 600; }
        .negative { color: #ef4444; font-weight: 600; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .model-grid, .results-summary, .day-details {
                grid-template-columns: 1fr;
            }
            .main-content { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>📊 Comprehensive Backtest</h1>
                <a href="/" class="back-btn">← Back to Dashboard</a>
            </div>
        </div>
        
        <div class="main-content">
            <div id="loadingMessage" class="message message-loading" style="display:none;"></div>
            <div id="errorMessage" class="message message-error" style="display:none;"></div>
            
            <form id="backtestForm">
                <!-- Section 1: Screening Model -->
                <div class="section">
                    <h2 class="section-title">
                        <span class="section-number">1</span>
                        Screening Model
                    </h2>
                    <p class="section-subtitle">
                        Select a model to screen and rank stocks daily. The backtester will pick the top N stocks each day.
                    </p>
                    
                    <div class="model-grid">
                        <!-- Technical Momentum -->
                        <div class="model-card" onclick="selectScreener('technical_momentum')">
                            <label>
                                <input type="radio" name="screener" value="technical_momentum" required>
                                <span class="model-name">📈 Technical Momentum</span>
                            </label>
                            <p class="model-description">
                                Finds stocks with strong RSI, MACD, volume surge, and price momentum. Best for trending opportunities.
                            </p>
                            <div class="model-params">
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">RSI Min</label>
                                        <input type="number" class="form-input" id="tm_rsi_min" value="40" min="0" max="100">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">RSI Max</label>
                                        <input type="number" class="form-input" id="tm_rsi_max" value="70" min="0" max="100">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Volume Min (x)</label>
                                        <input type="number" class="form-input" id="tm_volume" value="1.5" min="1" max="5" step="0.1">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Momentum %</label>
                                        <input type="number" class="form-input" id="tm_momentum" value="0.02" min="0.001" max="0.1" step="0.001">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Gap & Volatility -->
                        <div class="model-card" onclick="selectScreener('gap_volatility')">
                            <label>
                                <input type="radio" name="screener" value="gap_volatility">
                                <span class="model-name">🚀 Gap & Volatility</span>
                            </label>
                            <p class="model-description">
                                Targets gap-ups/downs with high volatility. Perfect for day trading gap-and-go setups.
                            </p>
                            <div class="model-params">
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">Min Gap %</label>
                                        <input type="number" class="form-input" id="gv_gap" value="0.02" min="0.001" max="0.1" step="0.001">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Min ATR %</label>
                                        <input type="number" class="form-input" id="gv_atr_min" value="2" min="0.5" max="10" step="0.5">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Max ATR %</label>
                                        <input type="number" class="form-input" id="gv_atr_max" value="8" min="1" max="20" step="0.5">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Trend Strength -->
                        <div class="model-card" onclick="selectScreener('trend_strength')">
                            <label>
                                <input type="radio" name="screener" value="trend_strength">
                                <span class="model-name">📊 Trend Strength</span>
                            </label>
                            <p class="model-description">
                                Identifies stocks in sustained trends with aligned moving averages. Great for momentum continuation.
                            </p>
                            <div class="model-params">
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">Min Trend Days</label>
                                        <input type="number" class="form-input" id="ts_days" value="3" min="1" max="10">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Min MA Separation %</label>
                                        <input type="number" class="form-input" id="ts_sep" value="0.02" min="0.001" max="0.1" step="0.001">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 2: Day Trading Model -->
                <div class="section">
                    <h2 class="section-title">
                        <span class="section-number">2</span>
                        Day Trading Model
                    </h2>
                    <p class="section-subtitle">
                        Choose a strategy for intraday entry and exit signals on the screened stocks.
                    </p>
                    
                    <div class="model-grid">
                        <!-- MA Crossover -->
                        <div class="model-card" onclick="selectDayModel('ma_crossover')">
                            <label>
                                <input type="radio" name="daymodel" value="ma_crossover" required>
                                <span class="model-name">📉 MA Crossover</span>
                            </label>
                            <p class="model-description">
                                Fast MA crosses slow MA with volume confirmation. Simple and effective.
                            </p>
                            <div class="model-params">
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">Fast Period</label>
                                        <input type="number" class="form-input" id="ma_fast" value="5" min="2" max="50">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Slow Period</label>
                                        <input type="number" class="form-input" id="ma_slow" value="20" min="5" max="200">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Volume Threshold</label>
                                        <input type="number" class="form-input" id="ma_volume" value="1.5" min="1" max="5" step="0.1">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Pattern Recognition -->
                        <div class="model-card" onclick="selectDayModel('pattern_recognition')">
                            <label>
                                <input type="radio" name="daymodel" value="pattern_recognition">
                                <span class="model-name">🎯 Pattern Recognition</span>
                            </label>
                            <p class="model-description">
                                Identifies 6 classic chart patterns: flags, head & shoulders, double tops/bottoms, triangles, cup & handle, engulfing.
                            </p>
                            <div class="model-params">
                                <div class="form-group">
                                    <label class="form-label">Min Confidence</label>
                                    <input type="number" class="form-input" id="pr_confidence" value="0.7" min="0.5" max="1" step="0.05">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Select Patterns:</label>
                                    <div class="pattern-selector">
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="bull_flag" checked> Bull Flag
                                        </label>
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="bear_flag" checked> Bear Flag
                                        </label>
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="head_shoulders" checked> H&S
                                        </label>
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="inverse_head_shoulders" checked> Inv H&S
                                        </label>
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="double_top" checked> Double Top
                                        </label>
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="double_bottom" checked> Double Bottom
                                        </label>
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="triangle_breakout" checked> Triangle
                                        </label>
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="cup_handle" checked> Cup & Handle
                                        </label>
                                        <label class="pattern-checkbox">
                                            <input type="checkbox" class="pattern-check" value="engulfing" checked> Engulfing
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- VWAP Bounce -->
                        <div class="model-card" onclick="selectDayModel('vwap_bounce')">
                            <label>
                                <input type="radio" name="daymodel" value="vwap_bounce">
                                <span class="model-name">💫 VWAP Bounce</span>
                            </label>
                            <p class="model-description">
                                Trades bounces off VWAP with volume confirmation. Mean-reversion strategy.
                            </p>
                            <div class="model-params">
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label class="form-label">VWAP Threshold</label>
                                        <input type="number" class="form-input" id="vw_threshold" value="0.002" min="0.001" max="0.01" step="0.001">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Volume Surge</label>
                                        <input type="number" class="form-input" id="vw_surge" value="1.5" min="1" max="5" step="0.1">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 3: Backtest Configuration -->
                <div class="section">
                    <h2 class="section-title">
                        <span class="section-number">3</span>
                        Backtest Configuration
                    </h2>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Top N Stocks per Day</label>
                            <input type="number" class="form-input" id="topN" value="3" min="1" max="10" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Min Score Threshold</label>
                            <input type="number" class="form-input" id="minScore" value="60" min="0" max="100" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Days to Test</label>
                            <input type="number" class="form-input" id="days" value="30" min="1" max="365" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Initial Capital ($)</label>
                            <input type="number" class="form-input" id="capital" value="10000" min="1000" max="1000000" required>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <label class="checkbox-group">
                            <input type="checkbox" id="forceExecution">
                            <span class="checkbox-label">Force Execution</span>
                        </label>
                        <p style="font-size: 13px; color: #6b7280; margin-top: 8px; margin-left: 26px;">
                            If checked, executes all signals regardless of confidence. If unchecked, only trades with confidence ≥ 70%.
                        </p>
                    </div>
                </div>
                
                <button type="submit" class="btn-primary" id="runBtn">Run Comprehensive Backtest</button>
            </form>
            
            <!-- Results Section -->
            <div id="resultsSection" class="results-section">
                <div class="section">
                    <h2 class="section-title">Backtest Results</h2>
                    
                    <!-- Summary Cards -->
                    <div class="results-summary" id="resultsSummary"></div>
                    
                    <!-- Daily Breakdown -->
                    <div class="daily-breakdown">
                        <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 16px;">Day-by-Day Breakdown</h3>
                        <div id="dailyBreakdown"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function selectScreener(model) {
            document.querySelectorAll('.model-card').forEach(card => {
                if (card.querySelector('input[name="screener"]')) {
                    card.classList.remove('selected');
                }
            });
            event.currentTarget.classList.add('selected');
            document.querySelector(`input[value="${model}"]`).checked = true;
        }
        
        function selectDayModel(model) {
            document.querySelectorAll('.model-card').forEach(card => {
                if (card.querySelector('input[name="daymodel"]')) {
                    card.classList.remove('selected');
                }
            });
            event.currentTarget.classList.add('selected');
            document.querySelector(`input[name="daymodel"][value="${model}"]`).checked = true;
        }
        
        document.getElementById('backtestForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const runBtn = document.getElementById('runBtn');
            const loadingMsg = document.getElementById('loadingMessage');
            const errorMsg = document.getElementById('errorMessage');
            const resultsSection = document.getElementById('resultsSection');
            
            resultsSection.style.display = 'none';
            errorMsg.style.display = 'none';
            
            runBtn.disabled = true;
            runBtn.textContent = 'Running Backtest...';
            loadingMsg.textContent = 'Running comprehensive backtest with daily screening... This may take 60-180 seconds.';
            loadingMsg.style.display = 'block';
            
            // Get selected models
            const screener = document.querySelector('input[name="screener"]:checked').value;
            const dayModel = document.querySelector('input[name="daymodel"]:checked').value;
            
            // Build screener params
            const screenerParams = {};
            if (screener === 'technical_momentum') {
                screenerParams.rsi_min = parseFloat(document.getElementById('tm_rsi_min').value);
                screenerParams.rsi_max = parseFloat(document.getElementById('tm_rsi_max').value);
                screenerParams.volume_min = parseFloat(document.getElementById('tm_volume').value);
                screenerParams.momentum_threshold = parseFloat(document.getElementById('tm_momentum').value);
            } else if (screener === 'gap_volatility') {
                screenerParams.min_gap = parseFloat(document.getElementById('gv_gap').value);
                screenerParams.min_atr_pct = parseFloat(document.getElementById('gv_atr_min').value);
                screenerParams.max_atr_pct = parseFloat(document.getElementById('gv_atr_max').value);
            } else if (screener === 'trend_strength') {
                screenerParams.min_trend_days = parseInt(document.getElementById('ts_days').value);
                screenerParams.min_ma_separation = parseFloat(document.getElementById('ts_sep').value);
            }
            
            // Build day model params
            const dayModelParams = {};
            if (dayModel === 'ma_crossover') {
                dayModelParams.fast_period = parseInt(document.getElementById('ma_fast').value);
                dayModelParams.slow_period = parseInt(document.getElementById('ma_slow').value);
                dayModelParams.volume_threshold = parseFloat(document.getElementById('ma_volume').value);
            } else if (dayModel === 'pattern_recognition') {
                dayModelParams.min_confidence = parseFloat(document.getElementById('pr_confidence').value);
                const patterns = Array.from(document.querySelectorAll('.pattern-check:checked')).map(cb => cb.value);
                dayModelParams.patterns = patterns;
            } else if (dayModel === 'vwap_bounce') {
                dayModelParams.vwap_threshold = parseFloat(document.getElementById('vw_threshold').value);
                dayModelParams.volume_surge = parseFloat(document.getElementById('vw_surge').value);
            }
            
            const params = {
                screener_model: screener,
                screener_params: screenerParams,
                day_model: dayModel,
                day_model_params: dayModelParams,
                top_n_stocks: parseInt(document.getElementById('topN').value),
                min_score: parseFloat(document.getElementById('minScore').value),
                force_execution: document.getElementById('forceExecution').checked,
                days: parseInt(document.getElementById('days').value),
                initial_capital: parseFloat(document.getElementById('capital').value)
            };
            
            try {
                const response = await fetch('/api/comprehensive-backtest', {
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
                resultsSection.scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                console.error('Error:', error);
                errorMsg.textContent = '❌ ' + error.message;
                errorMsg.style.display = 'block';
                loadingMsg.style.display = 'none';
            } finally {
                runBtn.disabled = false;
                runBtn.textContent = 'Run Comprehensive Backtest';
            }
        });
        
        function displayResults(results) {
            // Summary cards
            const summaryHTML = `
                <div class="result-card">
                    <div class="result-label">Total Return</div>
                    <div class="result-value ${results.total_return_pct >= 0 ? 'positive' : 'negative'}">
                        ${results.total_return_pct.toFixed(2)}%
                    </div>
                </div>
                <div class="result-card">
                    <div class="result-label">Final Value</div>
                    <div class="result-value">$${results.final_value.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Total Trades</div>
                    <div class="result-value">${results.total_trades}</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Win Rate</div>
                    <div class="result-value">${(results.win_rate * 100).toFixed(1)}%</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Profit Factor</div>
                    <div class="result-value ${results.profit_factor >= 1 ? 'positive' : 'negative'}">
                        ${results.profit_factor.toFixed(2)}
                    </div>
                </div>
                <div class="result-card">
                    <div class="result-label">Unique Stocks</div>
                    <div class="result-value">${results.unique_stocks_traded}</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Avg Win</div>
                    <div class="result-value positive">$${results.avg_win.toFixed(2)}</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Avg Loss</div>
                    <div class="result-value negative">$${results.avg_loss.toFixed(2)}</div>
                </div>
            `;
            document.getElementById('resultsSummary').innerHTML = summaryHTML;
            
            // Daily breakdown
            let dailyHTML = '';
            if (results.daily_results && results.daily_results.length > 0) {
                results.daily_results.forEach(day => {
                    const dayPnlClass = day.day_pnl >= 0 ? 'positive' : 'negative';
                    dailyHTML += `
                        <div class="day-card">
                            <div class="day-header">
                                <span class="day-date">📅 ${day.date}</span>
                                <span class="day-pnl ${dayPnlClass}">
                                    ${day.day_pnl >= 0 ? '+' : ''}$${day.day_pnl.toFixed(2)}
                                </span>
                            </div>
                            <div class="day-details">
                                <div class="day-stat">
                                    <strong>Screened:</strong> ${day.screened_count} stocks
                                </div>
                                <div class="day-stat">
                                    <strong>Entries:</strong> ${day.entries}
                                </div>
                                <div class="day-stat">
                                    <strong>Exits:</strong> ${day.exits}
                                </div>
                                <div class="day-stat">
                                    <strong>Ending Cash:</strong> $${day.ending_cash.toFixed(2)}
                                </div>
                            </div>
                            <div class="symbol-list">
                                <strong style="font-size: 13px; color: #6b7280;">Selected Stocks:</strong><br>
                                ${day.selected_symbols.map(s => `<span class="symbol-badge">${s}</span>`).join('')}
                            </div>
                        </div>
                    `;
                });
            }
            document.getElementById('dailyBreakdown').innerHTML = dailyHTML;
        }
    </script>
</body>
</html>
"""