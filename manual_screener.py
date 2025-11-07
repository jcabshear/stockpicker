"""
Manual Screening Model
Allows user to directly select stocks without automated screening
"""

from typing import List
from datetime import datetime


class ManualScreener:
    """Manual stock selection - user picks stocks directly"""
    
    def __init__(self, selected_symbols: List[str]):
        """
        Initialize with manually selected symbols
        
        Args:
            selected_symbols: List of stock symbols to trade (e.g., ['AAPL', 'TSLA', 'NVDA'])
        """
        self.name = "Manual Selection"
        self.selected_symbols = [s.strip().upper() for s in selected_symbols]
        self.client = None  # Set externally if needed
    
    def screen(self, universe: List[str] = None, min_score: float = 0) -> List[dict]:
        """
        Return manually selected stocks with 100 score
        
        Args:
            universe: Ignored for manual selection
            min_score: Ignored for manual selection
            
        Returns:
            List of dicts with symbol, score (always 100), and reason
        """
        results = []
        
        for symbol in self.selected_symbols:
            results.append({
                'symbol': symbol,
                'score': 100.0,  # Manual selections always get perfect score
                'reason': 'Manually selected by user',
                'metrics': {
                    'selection_method': 'manual',
                    'timestamp': datetime.now().isoformat()
                }
            })
        
        print(f"✓ Manual Selection: {len(results)} stocks")
        for stock in results:
            print(f"  • {stock['symbol']} - {stock['reason']}")
        
        return results
    
    def get_config(self) -> dict:
        """Get current configuration"""
        return {
            'model': 'manual',
            'symbols': self.selected_symbols,
            'count': len(self.selected_symbols)
        }
    
    def update_symbols(self, new_symbols: List[str]):
        """Update the list of manually selected symbols"""
        self.selected_symbols = [s.strip().upper() for s in new_symbols]
        print(f"✓ Updated manual selection: {', '.join(self.selected_symbols)}")


def create_manual_screener(symbols: str) -> ManualScreener:
    """
    Helper function to create manual screener from comma-separated string
    
    Args:
        symbols: Comma-separated string of symbols (e.g., "AAPL,TSLA,NVDA")
        
    Returns:
        ManualScreener instance
    """
    symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
    return ManualScreener(symbol_list)