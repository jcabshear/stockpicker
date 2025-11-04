from dataclasses import dataclass
from datetime import date

@dataclass
class RiskState:
    halted_today: bool = False
    last_day: date | None = None

state = RiskState()

def reset_if_new_day():
    """Reset daily risk state if it's a new day"""
    today = date.today()
    if state.last_day != today:
        state.halted_today = False
        state.last_day = today

def check_drawdown(today_pnl: float, max_daily_loss: float) -> bool:
    """
    Check if trading should continue based on daily drawdown.
    
    Args:
        today_pnl: Today's profit/loss (positive = profit, negative = loss)
        max_daily_loss: Maximum allowed loss for the day (positive number)
    
    Returns:
        True if trading should continue, False if halted
    """
    reset_if_new_day()
    
    if state.halted_today:
        return False
    
    # Check if loss exceeds maximum
    if -today_pnl >= max_daily_loss:
        state.halted_today = True
        print(f"🚨 TRADING HALTED: Daily loss limit reached (${-today_pnl:.2f} >= ${max_daily_loss:.2f})")
        return False
    
    return True