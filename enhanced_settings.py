"""
Enhanced Settings Page showing active models and configuration
"""

ENHANCED_SETTINGS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - Trading System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.98);
            padding: 24px 40px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .settings-btn {
            display: inline-flex;
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            text-decoration: none;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px 40px;
        }
        
        .settings-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        
        .settings-card {
            background: white;
            padding: 32px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 24px;
        }
        
        .card-icon {
            font-size: 32px;
            margin-right: 16px;
        }
        
        .card-title {
            font-size: 20px;
            font-weight: 600;
            color: #1a1a2e;
        }
        
        .active-badge {
            display: inline-block;
            padding: 4px 12px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-left: auto;
        }
        
        .model-display {
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 16px;
        }
        
        .model-name {
            font-size: 18px;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 8px;
        }
        
        .model-params {
            font-size: 14px;
            color: #666;
            line-height: 1.6;
        }
        
        .param-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }
        
        .param-row:last-child {
            border-bottom: none;
        }
        
        .param-label {
            font-weight: 600;
            color: #666;
        }
        
        .param-value {
            color: #1a1a2e;
        }
        
        .info-box {
            background: #e0e7ff;
            border-left: 4px solid #667eea;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
        }
        
        .info-box p {
            font-size: 14px;
            color: #4338ca;
            line-height: 1.6;
        }
        
        .last-updated {
            font-size: 12px;
            color: #999;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #e9ecef;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: #666;
            margin-bottom: 8px;
        }
        
        .form-input {
            width: 100%;
            padding: 12px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .btn-save {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn-save:hover {
            transform: translateY(-2px);
        }
        
        .success-message {
            background: #d1fae5;
            border: 2px solid #10b981;
            color: #065f46;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            display: none;
        }
        
        .success-message.visible {
            display: block;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1 style="font-size: 28px; font-weight: 700;">Trading Settings</h1>
            <div>
                <a href="/" class="settings-btn">📊 Dashboard</a>
                <a href="/backtest" class="settings-btn">🧪 Backtest</a>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="info-box">
            <p><strong>ℹ️ About These Settings:</strong> These are your currently active trading models and parameters. 
            To change them, run a backtest with your desired configuration and click "Publish to Live Trading".</p>
        </div>
        
        <div id="successMessage" class="success-message">
            Risk parameters updated successfully!
        </div>
        
        <div class="settings-grid">
            <!-- Active Screening Model -->
            <div class="settings-card">
                <div class="card-header">
                    <div class="card-icon">📊</div>
                    <h2 class="card-title">Screening Model</h2>
                    <span class="active-badge">ACTIVE</span>
                </div>
                
                <div class="model-display" id="screeningModel">
                    <div class="model-name">Loading...</div>
                    <div class="model-params" id="screeningParams"></div>
                </div>
                
                <div class="last-updated" id="screeningUpdated">
                    Loading...
                </div>
            </div>
            
            <!-- Active Day Trading Model -->
            <div class="settings-card">
                <div class="card-header">
                    <div class="card-icon">💹</div>
                    <h2 class="card-title">Day Trading Model</h2>
                    <span class="active-badge">ACTIVE</span>
                </div>
                
                <div class="model-display" id="daytradeModel">
                    <div class="model-name">Loading...</div>
                    <div class="model-params" id="daytradeParams"></div>
                </div>
                
                <div class="last-updated" id="daytradeUpdated">
                    Loading...
                </div>
            </div>
            
            <!-- Stock Selection Settings -->
            <div class="settings-card">
                <div class="card-header">
                    <div class="card-icon">🎯</div>
                    <h2 class="card-title">Stock Selection</h2>
                </div>
                
                <div class="model-params" id="selectionParams">
                    <div class="param-row">
                        <span class="param-label">Top N Stocks:</span>
                        <span class="param-value" id="topN">Loading...</span>
                    </div>
                    <div class="param-row">
                        <span class="param-label">Minimum Score:</span>
                        <span class="param-value" id="minScore">Loading...</span>
                    </div>
                    <div class="param-row">
                        <span class="param-label">Force Execution:</span>
                        <span class="param-value" id="forceExec">Loading...</span>
                    </div>
                </div>
            </div>
            
            <!-- Risk Management (Editable) -->
            <div class="settings-card">
                <div class="card-header">
                    <div class="card-icon">🛡️</div>
                    <h2 class="card-title">Risk Management</h2>
                </div>
                
                <form id="riskForm">
                    <div class="form-group">
                        <label class="form-label">Max USD Per Order</label>
                        <input type="number" id="maxOrder" class="form-input" placeholder="100">
                        <p style="font-size: 12px; color: #999; margin-top: 4px;">Maximum amount to invest per trade</p>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Max Daily Loss</label>
                        <input type="number" id="maxLoss" class="form-input" placeholder="50">
                        <p style="font-size: 12px; color: #999; margin-top: 4px;">Maximum loss allowed per day</p>
                    </div>
                    
                    <button type="submit" class="btn-save">💾 Save Risk Parameters</button>
                </form>
            </div>
        </div>
        
        <!-- Backtest Source Info -->
        <div class="settings-card" style="margin-top: 24px;" id="backtestSource">
            <div class="card-header">
                <div class="card-icon">🧪</div>
                <h2 class="card-title">Configuration Source</h2>
            </div>
            <div id="sourceInfo">
                Loading...
            </div>
        </div>
    </div>
    
    <script>
        // Load active configuration
        async function loadConfig() {
            try {
                const response = await fetch('/api/active-config');
                const config = await response.json();
                
                // Screening model
                document.querySelector('#screeningModel .model-name').textContent = formatModelName(config.screening.model);
                const screeningParamsHTML = Object.entries(config.screening.params).map(([key, value]) => 
                    `<div class="param-row">
                        <span class="param-label">${formatParamName(key)}:</span>
                        <span class="param-value">${value}</span>
                    </div>`
                ).join('');
                document.getElementById('screeningParams').innerHTML = screeningParamsHTML || '<em style="color: #999;">No parameters</em>';
                
                // Day trading model
                document.querySelector('#daytradeModel .model-name').textContent = formatModelName(config.daytrade.model);
                const daytradeParamsHTML = Object.entries(config.daytrade.params).map(([key, value]) => 
                    `<div class="param-row">
                        <span class="param-label">${formatParamName(key)}:</span>
                        <span class="param-value">${value}</span>
                    </div>`
                ).join('');
                document.getElementById('daytradeParams').innerHTML = daytradeParamsHTML || '<em style="color: #999;">No parameters</em>';
                
                // Selection params
                document.getElementById('topN').textContent = config.selection.top_n;
                document.getElementById('minScore').textContent = config.selection.min_score;
                document.getElementById('forceExec').textContent = config.selection.force_execution ? 'Yes' : 'No';
                
                // Risk params
                document.getElementById('maxOrder').value = config.risk.max_usd_per_order;
                document.getElementById('maxLoss').value = config.risk.max_daily_loss;
                
                // Last updated
                if (config.metadata.last_updated) {
                    const updated = new Date(config.metadata.last_updated).toLocaleString();
                    document.getElementById('screeningUpdated').textContent = `Last updated: ${updated}`;
                    document.getElementById('daytradeUpdated').textContent = `Last updated: ${updated}`;
                }
                
                // Backtest source
                if (config.metadata.backtest_source) {
                    const source = config.metadata.backtest_source;
                    document.getElementById('sourceInfo').innerHTML = `
                        <p style="margin-bottom: 8px;"><strong>Published from backtest:</strong></p>
                        <div class="param-row">
                            <span class="param-label">Backtest Period:</span>
                            <span class="param-value">${source.days} days</span>
                        </div>
                        <div class="param-row">
                            <span class="param-label">Initial Capital:</span>
                            <span class="param-value">$${source.initial_capital.toLocaleString()}</span>
                        </div>
                        <div class="param-row">
                            <span class="param-label">Published At:</span>
                            <span class="param-value">${new Date(source.published_at).toLocaleString()}</span>
                        </div>
                    `;
                } else {
                    document.getElementById('sourceInfo').innerHTML = '<em style="color: #999;">Not published from a backtest yet</em>';
                }
                
            } catch (error) {
                console.error('Error loading config:', error);
            }
        }
        
        // Format model name
        function formatModelName(name) {
            return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        }
        
        // Format parameter name
        function formatParamName(name) {
            return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        }
        
        // Save risk parameters
        document.getElementById('riskForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const maxOrder = parseFloat(document.getElementById('maxOrder').value);
            const maxLoss = parseFloat(document.getElementById('maxLoss').value);
            
            try {
                const response = await fetch('/api/update-risk-params', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        max_usd_per_order: maxOrder,
                        max_daily_loss: maxLoss
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to update');
                }
                
                // Show success message
                const successMsg = document.getElementById('successMessage');
                successMsg.classList.add('visible');
                setTimeout(() => successMsg.classList.remove('visible'), 3000);
                
                // Reload config
                await loadConfig();
                
            } catch (error) {
                console.error('Error updating risk params:', error);
                alert('Failed to update risk parameters. Please try again.');
            }
        });
        
        // Initial load
        loadConfig();
        
        // Refresh every 30 seconds
        setInterval(loadConfig, 30000);
    </script>
</body>
</html>
"""