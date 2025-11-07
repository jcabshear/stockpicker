import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Alpaca credentials
    alpaca_key: str = os.getenv('ALPACA_KEY', '')
    alpaca_secret: str = os.getenv('ALPACA_SECRET', '')
    alpaca_key: str = (
        os.getenv('ALPACA_KEY')
        or os.getenv('APCA_API_KEY_ID')
        or ''
    )
    alpaca_secret: str = (
        os.getenv('ALPACA_SECRET')
        or os.getenv('APCA_API_SECRET_KEY')
        or ''
    )
    paper: bool = os.getenv('PAPER', 'true').lower() == 'true'
    

    # Trading parameters
    allow_trading: bool = os.getenv('ALLOW_TRADING', 'false').lower() == 'true'
    max_usd_per_order: float = float(os.getenv('MAX_USD_PER_ORDER', '100'))
    max_daily_loss: float = float(os.getenv('MAX_DAILY_LOSS', '50'))
    feed: str = os.getenv('FEED', 'iex')
    symbols: str = os.getenv('SYMBOLS', 'AAPL,MSFT,GOOGL')
    

    # Auto stock selection
    auto_select_stocks: bool = os.getenv('AUTO_SELECT_STOCKS', 'true').lower() == 'true'
    min_stock_score: float = float(os.getenv('MIN_STOCK_SCORE', '60'))
    

    # Strategy parameters
    short_window: int = int(os.getenv('SHORT_WINDOW', '5'))
    long_window: int = int(os.getenv('LONG_WINDOW', '20'))
    volume_threshold: float = float(os.getenv('VOLUME_THRESHOLD', '1.5'))
    stop_loss_pct: float = float(os.getenv('STOP_LOSS_PCT', '0.02'))
    

    # Mode
    mode: str = "live"
    

    class Config:
        case_sensitive = False


settings = Settings()


# Validate
if not settings.alpaca_key or not settings.alpaca_secret:
    print("⚠️  ERROR: Alpaca credentials not found!")
    print("   Set ALPACA_KEY and ALPACA_SECRET in Render Environment")
    raise ValueError("Missing Alpaca API credentials")
    raise ValueError("Missing Alpaca API credentials")


# Ensure downstream Alpaca clients that rely on standard environment variables work
os.environ.setdefault('ALPACA_KEY', settings.alpaca_key)
os.environ.setdefault('ALPACA_SECRET', settings.alpaca_secret)
os.environ.setdefault('APCA_API_KEY_ID', settings.alpaca_key)
os.environ.setdefault('APCA_API_SECRET_KEY', settings.alpaca_secret)