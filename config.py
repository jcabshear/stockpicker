import os
from pydantic import BaseModel

class Settings(BaseModel):
    alpaca_key: str = os.environ["APCA_API_KEY_ID"]
    alpaca_secret: str = os.environ["APCA_API_SECRET_KEY"]
    paper: bool = os.environ.get("APCA_PAPER", "true").lower() == "true"
    symbols: list[str] = os.environ.get("SYMBOLS", "SPY").split(",")
    max_usd_per_order: float = float(os.environ.get("MAX_USD_PER_ORDER", "500"))
    max_daily_loss: float = float(os.environ.get("MAX_DAILY_LOSS", "100"))
    allow_trading: bool = os.environ.get("ALLOW_TRADING", "true").lower() == "true"
    feed: str = os.environ.get("DATA_FEED", "iex")  # use "iex" for paper

settings = Settings()
