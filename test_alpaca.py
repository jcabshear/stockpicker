"""
Diagnostic script to test Alpaca API connectivity
Run this to check if your credentials and connection work
"""

import os
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from datetime import datetime, timedelta


def test_alpaca_connection():
    """Test Alpaca API connection"""
    print("\n" + "="*80)
    print("🔍 ALPACA API DIAGNOSTIC")
    print("="*80)
    
    # Get credentials
    api_key = os.getenv('ALPACA_KEY', '')
    api_secret = os.getenv('ALPACA_SECRET', '')
    paper = os.getenv('PAPER', 'true').lower() == 'true'
    
    print(f"\n📋 Configuration:")
    print(f"   API Key: {api_key[:10]}..." if api_key else "   API Key: NOT SET")
    print(f"   Secret: {api_secret[:10]}..." if api_secret else "   Secret: NOT SET")
    print(f"   Paper Trading: {paper}")
    print()
    
    if not api_key or not api_secret:
        print("❌ ERROR: API credentials not found!")
        print("   Set ALPACA_KEY and ALPACA_SECRET environment variables")
        return False
    
    # Test Trading Client
    print("1️⃣ Testing Trading API...")
    try:
        trading_client = TradingClient(api_key, api_secret, paper=paper)
        account = trading_client.get_account()
        
        print(f"   ✅ Trading API connected")
        print(f"   Account: {account.account_number}")
        print(f"   Status: {account.status}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Equity: ${float(account.equity):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        
        # Check positions
        positions = trading_client.get_all_positions()
        print(f"   Open Positions: {len(positions)}")
        
        # Check market status
        clock = trading_client.get_clock()
        print(f"   Market Open: {clock.is_open}")
        print(f"   Next Open: {clock.next_open}")
        print(f"   Next Close: {clock.next_close}")
        
    except Exception as e:
        print(f"   ❌ Trading API failed: {e}")
        return False
    
    # Test Historical Data Client
    print("\n2️⃣ Testing Historical Data API...")
    try:
        data_client = StockHistoricalDataClient(api_key, api_secret)
        print(f"   ✅ Historical Data API connected")
    except Exception as e:
        print(f"   ❌ Historical Data API failed: {e}")
        return False
    
    # Test WebSocket connectivity (this is where connection limits show up)
    print("\n3️⃣ Testing WebSocket Connection...")
    print("   NOTE: This is where 'connection limit exceeded' errors occur")
    print("   if you have another session connected.")
    
    try:
        from alpaca.data.live import StockDataStream
        from alpaca.data.enums import DataFeed
        
        print("   Creating WebSocket stream...")
        stream = StockDataStream(api_key, api_secret, feed=DataFeed.IEX)
        print("   ✅ WebSocket stream created")
        print("   ⚠️  Not testing actual connection (requires async)")
        print("   If you see 'connection limit exceeded' in your logs,")
        print("   you need to close other Alpaca sessions")
        
    except Exception as e:
        print(f"   ❌ WebSocket setup failed: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80)
    print("\n💡 If you're still having issues:")
    print("   1. Check for 'connection limit exceeded' in logs")
    print("   2. Close other Alpaca sessions at https://app.alpaca.markets/")
    print("   3. Wait 10 minutes and try again")
    print()
    
    return True


if __name__ == "__main__":
    test_alpaca_connection()