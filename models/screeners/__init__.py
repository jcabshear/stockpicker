"""
Screeners Package
Exports all screening models and factory function
"""

from .base_screener import BaseScreener, ScreenedStock
from .technical_momentum import TechnicalMomentumScreener
from .gap_volatility import GapVolatilityScreener
from .trend_strength import TrendStrengthScreener


def get_screener(model_name: str, api_key: str, api_secret: str, **kwargs) -> BaseScreener:
    """Factory function to get screener by name"""
    screeners = {
        'technical_momentum': TechnicalMomentumScreener,
        'gap_volatility': GapVolatilityScreener,
        'trend_strength': TrendStrengthScreener
    }
    
    screener_class = screeners.get(model_name.lower())
    if not screener_class:
        raise ValueError(f"Unknown screener: {model_name}. Available: {list(screeners.keys())}")
    
    return screener_class(api_key, api_secret, **kwargs)


__all__ = [
    'BaseScreener',
    'ScreenedStock',
    'TechnicalMomentumScreener',
    'GapVolatilityScreener',
    'TrendStrengthScreener',
    'get_screener'
]
