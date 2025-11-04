from dataclasses import dataclass
from datetime import date

@dataclass
class RiskState:
    halted_today: bool = False
    last_day: date | None = None

state = RiskState()

def reset_if_new_day(today_pnl: float):
    today = date.today()
    if state.last_day != today:
        state.halted_today = False
        state.last_day = today

def check_drawdown(today_pnl: float, max_daily_loss: float) -> bool:
    reset_if_new_day(today_pnl)
    if state.halted_today:
        return False
    if -today_pnl >= max_daily_loss:
        state.halted_today = True
        return False
    return True
