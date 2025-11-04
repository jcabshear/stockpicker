import asyncio
from collections import deque
from statistics import fmean

from fastapi import FastAPI, HTTPException
import uvicorn

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import TimeInForce, OrderSide, OrderClass
from alpaca.data.live import StockDataStream
from alpaca.data.enums import DataFeed

from config import settings
from risk import check_drawdown
from screener import DailyGainScreener

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {
        "status": "running",
        "mode": settings.mode,
        "daily_pnl": trader.daily_pnl,
        "positions": len(trader.positions)
    }

@app.get("/positions")
def get_positions():
    return {
        "positions": [
            {
                "symbol": p.symbol,
                "shares": p.shares,
                "pnl": p.pnl,
                "pnl_pct": p.pnl_pct
            }
            for p in trader.positions.values()
        ]
    }

# Run both HTTP server and trading
async def run_all():
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    
    await asyncio.gather(
        server.serve(),
        trader.run(symbols)
    )

# ---- toy SMA crossover parameters ----
WINDOW_SHORT = 5
WINDOW_LONG = 20

bars: dict[str, deque] = {}
pnl_today = 0.0

app = FastAPI()
allow_trading_flag = settings.allow_trading

# Global screener instance
screener = DailyGainScreener()
daily_picks: list = []


# ---------- admin endpoints (local to worker) ----------
@app.post("/kill")
def kill(token: str):
    global allow_trading_flag
    if token != "let-me-in":
        raise HTTPException(status_code=401, detail="bad token")
    allow_trading_flag = False
    return {"ok": True}

@app.get("/health")
def health():
    return {"ok": True, "allow_trading": allow_trading_flag}

@app.get("/screen")
async def run_screener(top_n: int = 20):
    """Run the stock screener and return top picks"""
    global daily_picks
    
    watchlist = [
        # Mega Cap Tech
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NVDA", "AVGO", "ORCL",
        "ADBE", "CRM", "CSCO", "ACN", "IBM", "INTC", "AMD", "QCOM", "TXN", "AMAT",
        "INTU", "NOW", "PANW", "SNPS", "CDNS", "ADSK", "MCHP", "KLAC", "LRCX", "NXPI",
        
        # Communication & Media
        "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR", "EA", "TTWO", "WBD",
        "SPOT", "RBLX", "U", "MTCH", "PINS", "SNAP", "ROKU", "PARA", "FOXA", "NWS",
        
        # Finance
        "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "SPGI",
        "CB", "PGR", "TFC", "USB", "PNC", "BK", "COF", "AFL", "MET", "PRU",
        "AIG", "ALL", "TRV", "AMP", "SOFI", "AFRM", "UPST", "LC", "SQ", "PYPL",
        
        # Healthcare & Biotech
        "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "BMY",
        "AMGN", "GILD", "CVS", "CI", "VRTX", "REGN", "ISRG", "SYK", "BSX", "MDT",
        "ELV", "ZTS", "DXCM", "HUM", "BDX", "EW", "IDXX", "RMD", "MTD", "IQV",
        
        # Consumer Discretionary
        "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "CMG",
        "MAR", "HLT", "ABNB", "GM", "F", "RIVN", "LCID", "NIO", "LI", "XPEV",
        "DASH", "UBER", "LYFT", "CVNA", "RH", "ETSY", "W", "CHWY",
        
        # Consumer Staples
        "PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "EL", "CL", "MDLZ",
        
        # Energy
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
        
        # Industrials
        "BA", "CAT", "UPS", "RTX", "HON", "LMT", "GE", "DE", "UNP", "MMM",
        
        # High Growth
        "COIN", "HOOD", "PLTR", "SNOW", "DDOG", "NET", "CRWD", "ZS", "OKTA", "MDB",
        
        # EVs & Clean Energy
        "ENPH", "SEDG", "RUN", "PLUG", "FCEL", "BE", "BLNK",
    ]
    
    results = await screener.screen_stocks(symbols=watchlist, top_n=top_n)
    daily_picks = results
    
    return {
        "timestamp": asyncio.get_event_loop().time(),
        "count": len(results),
        "stocks": [
            {
                "symbol": s.symbol,
                "score": s.score,
                "price": s.price,
                "premarket_change": s.premarket_change,
                "volume_ratio": s.volume_ratio,
                "rsi": s.rsi,
                "reasons": s.reasons
            }
            for s in results
        ]
    }

@app.get("/picks")
def get_daily_picks():
    """Get the current daily picks from last screen"""
    return {
        "count": len(daily_picks),
        "stocks": [
            {
                "symbol": s.symbol,
                "score": s.score,
                "price": s.price,
                "premarket_change": s.premarket_change,
                "volume_ratio": s.volume_ratio,
                "rsi": s.rsi,
                "reasons": s.reasons
            }
            for s in daily_picks
        ]
    }


# ---------- http server ----------
async def run_http():
    config = uvicorn.Config(app, host="0.0.0.0", port=10000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


# ---------- trading helpers ----------
def trading_client() -> TradingClient:
    return TradingClient(settings.alpaca_key, settings.alpaca_secret, paper=settings.paper)

async def submit_usd_market(symbol: str, usd: float, side: OrderSide):
    if not allow_trading_flag:
        return
    client = trading_client()
    req = MarketOrderRequest(
        symbol=symbol,
        notional=usd,
        side=side,
        time_in_force=TimeInForce.DAY,
        order_class=OrderClass.Simple,
    )
    try:
        client.submit_order(req)
        print(f"order sent {side.name} {symbol} ${usd}")
    except Exception as e:
        print("submit error:", e)


# ---------- signal ----------
def signal(symbol: str) -> str | None:
    q = bars.setdefault(symbol, deque(maxlen=WINDOW_LONG))
    if len(q) < WINDOW_LONG:
        return None
    short = fmean(list(q)[-WINDOW_SHORT:])
    long = fmean(q)
    if short > long:
        return "buy"
    if short < long:
        return "sell"
    return None


# ---------- streaming loop ----------
async def stream_task():
    # map env var string to the enum Alpaca expects
    feed_map = {"iex": DataFeed.IEX, "sip": DataFeed.SIP}
    feed_enum = feed_map.get(settings.feed.lower(), DataFeed.IEX)

    def handle_bar(bar):
        symbol = bar.symbol
        q = bars.setdefault(symbol, deque(maxlen=WINDOW_LONG))
        q.append(bar.close)

        if not check_drawdown(pnl_today, settings.max_daily_loss):
            return

        sig = signal(symbol)
        if sig == "buy":
            asyncio.create_task(submit_usd_market(symbol, settings.max_usd_per_order, OrderSide.BUY))
        elif sig == "sell":
            asyncio.create_task(submit_usd_market(symbol, settings.max_usd_per_order, OrderSide.SELL))

    # resilient loop: recreate the stream if the socket drops
    while True:
        try:
            stream = StockDataStream(
                settings.alpaca_key,
                settings.alpaca_secret,
                feed=feed_enum,
            )

            # Use daily picks if available, otherwise use default symbols
            symbols_to_trade = [s.symbol for s in daily_picks] if daily_picks else settings.symbols
            
            # subscribe for each symbol
            for s in symbols_to_trade:
                stream.subscribe_bars(handle_bar, s.strip())

            print(f"subscribed to bars for {len(symbols_to_trade)} symbols on feed {feed_enum.name.lower()}")
            await stream.run()  # blocks until stopped or error
        except Exception as e:
            print("stream loop error:", repr(e))
            await asyncio.sleep(3)


# ---------- scheduled screener task ----------
async def scheduled_screener():
    """Run screener at market open (9:30 AM ET)"""
    while True:
        from datetime import datetime
        import pytz
        
        now = datetime.now(pytz.timezone('US/Eastern'))
        
        # Run screener at 9:15 AM ET (before market open)
        if now.hour == 9 and now.minute == 15:
            print("Running daily screener...")
            try:
                await run_screener(top_n=20)
                print(f"Screener complete! Found {len(daily_picks)} stocks")
            except Exception as e:
                print(f"Screener error: {e}")
            
            # Sleep for an hour to avoid running multiple times
            await asyncio.sleep(3600)
        else:
            # Check every minute
            await asyncio.sleep(60)


# ---------- optional heartbeat so logs show liveness ----------
async def heartbeat():
    while True:
        print("bot alive")
        await asyncio.sleep(30)


# ---------- entry ----------
async def main():
    await asyncio.gather(
        run_http(), 
        stream_task(), 
        heartbeat(),
        scheduled_screener()  # Add scheduled screener
    )

if __name__ == "__main__":
    asyncio.run(main())