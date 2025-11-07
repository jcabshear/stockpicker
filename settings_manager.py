"""
Settings Manager
Handles publishing backtest configurations to live trading
"""

import json
import os
from typing import Dict
from datetime import datetime


class TradingSettingsManager:
    """Manage live trading settings and publish from backtests"""
    
    def __init__(self, settings_file: str = '/home/claude/live_trading_settings.json'):
        self.settings_file = settings_file
        self.load_settings()
    
    def load_settings(self) -> Dict:
        """Load current live trading settings"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                self.current_settings = json.load(f)
        else:
            # Default settings
            self.current_settings = {
                'screening_model': 'technical_momentum',
                'screening_params': {},
                'daytrade_model': 'ma_crossover',
                'daytrade_params': {},
                'top_n_stocks': 3,
                'min_score': 60,
                'force_execution': False,
                'max_usd_per_order': 100,
                'max_daily_loss': 50,
                'last_updated': None,
                'backtest_source': None
            }
        return self.current_settings
    
    def save_settings(self):
        """Save settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.current_settings, f, indent=2)
    
    def publish_backtest_settings(self, backtest_config: Dict) -> Dict:
        """
        Publish backtest configuration to live trading
        
        Args:
            backtest_config: Dict containing:
                - screener_model: str
                - screener_params: dict
                - day_model: str
                - day_model_params: dict
                - top_n_stocks: int
                - min_score: float
                - force_execution: bool
                
        Returns:
            Dict with status and updated settings
        """
        try:
            # Validate config
            required_keys = ['screener_model', 'day_model']
            for key in required_keys:
                if key not in backtest_config:
                    raise ValueError(f"Missing required key: {key}")
            
            # Update current settings
            self.current_settings['screening_model'] = backtest_config['screener_model']
            self.current_settings['screening_params'] = backtest_config.get('screener_params', {})
            self.current_settings['daytrade_model'] = backtest_config['day_model']
            self.current_settings['daytrade_params'] = backtest_config.get('day_model_params', {})
            self.current_settings['top_n_stocks'] = backtest_config.get('top_n_stocks', 3)
            self.current_settings['min_score'] = backtest_config.get('min_score', 60)
            self.current_settings['force_execution'] = backtest_config.get('force_execution', False)
            
            # Add metadata
            self.current_settings['last_updated'] = datetime.now().isoformat()
            self.current_settings['backtest_source'] = {
                'days': backtest_config.get('days', 30),
                'initial_capital': backtest_config.get('initial_capital', 10000),
                'published_at': datetime.now().isoformat()
            }
            
            # Save to file
            self.save_settings()
            
            return {
                'status': 'success',
                'message': 'Backtest settings published to live trading',
                'settings': self.current_settings
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to publish settings: {str(e)}'
            }
    
    def get_active_config(self) -> Dict:
        """Get currently active trading configuration"""
        return {
            'screening': {
                'model': self.current_settings['screening_model'],
                'params': self.current_settings['screening_params']
            },
            'daytrade': {
                'model': self.current_settings['daytrade_model'],
                'params': self.current_settings['daytrade_params']
            },
            'selection': {
                'top_n': self.current_settings['top_n_stocks'],
                'min_score': self.current_settings['min_score'],
                'force_execution': self.current_settings['force_execution']
            },
            'risk': {
                'max_usd_per_order': self.current_settings.get('max_usd_per_order', 100),
                'max_daily_loss': self.current_settings.get('max_daily_loss', 50)
            },
            'metadata': {
                'last_updated': self.current_settings.get('last_updated'),
                'backtest_source': self.current_settings.get('backtest_source')
            }
        }
    
    def update_risk_params(self, max_usd_per_order: float = None, max_daily_loss: float = None):
        """Update risk parameters"""
        if max_usd_per_order is not None:
            self.current_settings['max_usd_per_order'] = max_usd_per_order
        if max_daily_loss is not None:
            self.current_settings['max_daily_loss'] = max_daily_loss
        
        self.current_settings['last_updated'] = datetime.now().isoformat()
        self.save_settings()
    
    def format_for_display(self) -> str:
        """Format current settings for display"""
        config = self.get_active_config()
        
        output = []
        output.append("=== ACTIVE TRADING CONFIGURATION ===\n")
        
        output.append("📊 SCREENING MODEL:")
        output.append(f"  Model: {config['screening']['model']}")
        if config['screening']['params']:
            output.append(f"  Parameters: {json.dumps(config['screening']['params'], indent=4)}")
        output.append("")
        
        output.append("💹 DAY TRADING MODEL:")
        output.append(f"  Model: {config['daytrade']['model']}")
        if config['daytrade']['params']:
            output.append(f"  Parameters: {json.dumps(config['daytrade']['params'], indent=4)}")
        output.append("")
        
        output.append("🎯 STOCK SELECTION:")
        output.append(f"  Top N Stocks: {config['selection']['top_n']}")
        output.append(f"  Minimum Score: {config['selection']['min_score']}")
        output.append(f"  Force Execution: {config['selection']['force_execution']}")
        output.append("")
        
        output.append("🛡️ RISK MANAGEMENT:")
        output.append(f"  Max USD Per Order: ${config['risk']['max_usd_per_order']}")
        output.append(f"  Max Daily Loss: ${config['risk']['max_daily_loss']}")
        output.append("")
        
        if config['metadata']['last_updated']:
            output.append(f"Last Updated: {config['metadata']['last_updated']}")
        if config['metadata']['backtest_source']:
            output.append(f"Published from backtest: {json.dumps(config['metadata']['backtest_source'], indent=2)}")
        
        return '\n'.join(output)


# Global instance
settings_manager = TradingSettingsManager()