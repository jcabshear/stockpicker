# Alpaca Trading Bot on Render

A minimal 24x7 worker that connects to Alpaca Market Data, runs a simple SMA signal, and submits paper orders.

## Deploy
1. Push this repo to GitHub.
2. Create a Background Worker in Render pointing at the repo.
3. Set env vars:
   - APCA_API_KEY_ID
   - APCA_API_SECRET_KEY
   - APCA_PAPER=true
   - SYMBOLS=SPY
   - MAX_USD_PER_ORDER=100
   - MAX_DAILY_LOSS=50
   - DATA_FEED=iex
   - ALLOW_TRADING=true
4. Deploy and watch logs.
5. Health check: GET `/health`
6. Kill switch: POST `/kill?token=let-me-in`
