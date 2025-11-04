from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Alpaca credentials
    alpaca_key: str
    alpaca_secret: str
    paper: bool = True
    
    # Trading parameters
    allow_trading: bool = True
    max_usd_per_order: float = 1000.0
    max_daily_loss: float = 500.0
    feed: str = "iex"
    
    # Strategy parameters
    short_window: int = 5
    long_window: int = 20
    volume_threshold: float = 1.5
    stop_loss_pct: float = 0.02
    
    # Mode
    mode: str = "backtest"  # "backtest" or "live"
    
    class Config:
        env_file = ".env"

settings = Settings()