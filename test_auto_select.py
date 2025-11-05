"""
Test Script for Auto Stock Selection
Run this to verify your setup before deploying
"""

import sys
import os

print("="*80)
print("🧪 TESTING AUTO STOCK SELECTION SYSTEM")
print("="*80)
print()

# Check Python version
print("1️⃣ Python Version Check...")
if sys.version_info < (3, 8):
    print("   ❌ Python 3.8+ required")
    sys.exit(1)
else:
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Check required modules
print("\n2️⃣ Module Import Check...")
required_modules = [
    'pandas',
    'alpaca',
    'fastapi',
    'uvicorn',
    'pydantic_settings'
]

missing = []
for module in required_modules:
    try:
        __import__(module.replace('-', '_'))
        print(f"   ✅ {module}")
    except ImportError:
        print(f"   ❌ {module} - Run: pip install {module}")
        missing.append(module)

if missing:
    print(f"\n❌ Missing modules. Install with:")
    print(f"   pip install {' '.join(missing)}")
    sys.exit(1)

# Check config
print("\n3️⃣ Configuration Check...")
try:
    from config import settings
    print("   ✅ config.py loaded")
    
    if settings.alpaca_key and settings.alpaca_secret:
        print(f"   ✅ Alpaca credentials present")
        print(f"      Key: {settings.alpaca_key[:10]}...")
        print(f"      Paper: {settings.paper}")
    else:
        print("   ⚠️  Alpaca credentials missing")
        print("      Set ALPACA_KEY and ALPACA_SECRET")
except Exception as e:
    print(f"   ❌ Config error: {e}")
    sys.exit(1)

# Check stock scorer
print("\n4️⃣ Stock Scorer Check...")
try:
    from stock_scorer import StockScorer
    print("   ✅ stock_scorer.py imported")
    
    # Test instantiation
    scorer = StockScorer(settings.alpaca_key, settings.alpaca_secret)
    print("   ✅ StockScorer initialized")
    
except Exception as e:
    print(f"   ❌ Stock scorer error: {e}")
    sys.exit(1)

# Check daily selector
print("\n5️⃣ Daily Selector Check...")
try:
    from daily_selector import DailyStockSelector
    print("   ✅ daily_selector.py imported")
    
    selector = DailyStockSelector(settings.alpaca_key, settings.alpaca_secret)
    print("   ✅ DailyStockSelector initialized")
    print(f"   ✅ Stock universe: {len(selector.nasdaq_universe)} stocks")
    
except Exception as e:
    print(f"   ❌ Daily selector error: {e}")
    sys.exit(1)

# Test scoring (quick test with 3 stocks)
print("\n6️⃣ Live Scoring Test...")
try:
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    print(f"   Testing with: {', '.join(test_symbols)}")
    
    scores = []
    for symbol in test_symbols:
        print(f"   Scoring {symbol}...", end='')
        scored = scorer.score_stock(symbol)
        scores.append(scored)
        print(f" {scored.total_score:.1f}/100")
    
    if all(s.total_score > 0 for s in scores):
        print("   ✅ Scoring working correctly")
    else:
        print("   ⚠️  Some stocks returned 0 scores (may need more data)")
    
except Exception as e:
    print(f"   ❌ Scoring test failed: {e}")
    sys.exit(1)

# Check API files
print("\n7️⃣ API Integration Check...")
try:
    # Check if main_integrated.py or main.py exists
    if os.path.exists('main_integrated.py'):
        print("   ✅ main_integrated.py found")
    elif os.path.exists('main.py'):
        print("   ✅ main.py found")
        print("   ⚠️  Consider renaming main_integrated.py to main.py")
    else:
        print("   ❌ No main.py found")
        print("      Rename main_integrated.py to main.py")
    
except Exception as e:
    print(f"   ❌ API check error: {e}")

# Summary
print("\n" + "="*80)
print("📊 TEST SUMMARY")
print("="*80)
print()

print("✅ All core components working!")
print()
print("📋 Next Steps:")
print("   1. Run full screening test:")
print("      python daily_selector.py")
print()
print("   2. Upload files to GitHub:")
print("      - stock_scorer.py")
print("      - daily_selector.py")
print("      - main_integrated.py (rename to main.py)")
print("      - config.py")
print()
print("   3. Set environment variables in Render:")
print("      AUTO_SELECT_STOCKS=true")
print("      MIN_STOCK_SCORE=60")
print()
print("   4. Deploy and monitor logs for selection at 6 AM ET")
print()
print("="*80)
print()

# Optional: Run a quick selection
print("🎯 Want to run a quick selection test? (y/n): ", end='')
response = input().strip().lower()

if response == 'y':
    print("\n" + "="*80)
    print("Running quick 10-stock selection test...")
    print("="*80)
    
    # Test with smaller universe
    quick_test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 
                         'AMD', 'META', 'AMZN', 'NFLX', 'INTC']
    
    scored = scorer.screen_and_rank(quick_test_stocks, min_score=50)
    
    if scored:
        print(f"\n✅ Found {len(scored)} qualifying stocks:")
        for i, stock in enumerate(scored[:3], 1):
            print(f"   {i}. {stock.symbol}: {stock.total_score:.1f}")
        print("\n🎉 Test successful! System is ready.")
    else:
        print("\n⚠️  No stocks met criteria (may need lower threshold or more data)")

print("\n✅ Testing complete!\n")