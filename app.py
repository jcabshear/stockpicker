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

# ---- toy SMA crossover parameters ----
WINDOW_SHORT = 5
WINDOW_LONG = 20

bars: dict[str, deque] = {}
pnl_today = 0.0

app = FastAPI()
allow_trading_flag = settings.allow_trading


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

    async def handle_bar(bar):
        symbol = bar.symbol
        q = bars.setdefault(symbol, deque(maxlen=WINDOW_LONG))
        q.append(bar.close)

        if not check_drawdown(pnl_today, settings.max_daily_loss):
            return

        sig = signal(symbol)
        if sig == "buy":
            await submit_usd_market(symbol, settings.max_usd_per_order, OrderSide.BUY)
        elif sig == "sell":
            await submit_usd_market(symbol, settings.max_usd_per_order, OrderSide.SELL)

    # resilient loop: recreate the stream if the socket drops
    while True:
        try:
            stream = StockDataStream(
                settings.alpaca_key,
                settings.alpaca_secret,
                feed=feed_enum,
            )

            # subscribe for each symbol
            for s in settings.symbols:
                stream.subscribe_bars(handle_bar, s.strip())

            print(f"subscribed to bars for {settings.symbols} on feed {feed_enum.name.lower()}")
            await stream.run()  # blocks until stopped or error
        except Exception as e:
            print("stream loop error:", repr(e))
            await asyncio.sleep(3)
        # do not call stream.stop() here; some versions return None internals
        # simply loop and rebuild the stream


# ---------- optional heartbeat so logs show liveness ----------
async def heartbeat():
    while True:
        print("bot alive")
        await asyncio.sleep(30)


# ---------- entry ----------
async def main():
    await asyncio.gather(run_http(), stream_task(), heartbeat())

if __name__ == "__main__":
    asyncio.run(main())
