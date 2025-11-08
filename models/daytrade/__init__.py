"""
Day Trading Models Package
Exports all intraday trading models and factory function
"""

from .base_model import BaseDayTradeModel, TradeSignal
from .ma_crossover import MovingAverageCrossover
from .vwap_bounce import VWAPBounce
from .pattern_recognition import PatternRecognition


def get_day_trade_model(model_name: str, **kwargs) -> BaseDayTradeModel:
    """Factory function to get day trade model by name"""
    models = {
        'ma_crossover': MovingAverageCrossover,
        'vwap_bounce': VWAPBounce,
        'pattern_recognition': PatternRecognition,
        # Aliases for UI compatibility
        'vwap_mean_reversion': VWAPBounce,
        'momentum_breakout': PatternRecognition
    }
    
    model_class = models.get(model_name.lower())
    if not model_class:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(set(models.keys()))}")
    
    return model_class(**kwargs)


__all__ = [
    'BaseDayTradeModel',
    'TradeSignal',
    'MovingAverageCrossover',
    'VWAPBounce',
    'PatternRecognition',
    'get_day_trade_model'
]
