"""
Automated Daily Stock Selector
Runs screening before market open and updates trading symbols
"""

import asyncio
from datetime import datetime, time
from typing import List
from stock_scorer import StockScorer, ScoredStock
from config import settings


class DailyStockSelector:
    """Automatically select best stocks each trading day"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.scorer = StockScorer(api_key, api_secret)
        self.last_selection_date = None
        self.current_symbols = []
        
        # NASDAQ universe to screen
        # You can expand this list or pull from an API
        self.nasdaq_universe = [
            # Mega caps
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AVGO',
            
            # Large caps
            'AMD', 'NFLX', 'INTC', 'CSCO', 'ADBE', 'PYPL', 'CMCSA', 'PEP',
            'TXN', 'QCOM', 'COST', 'SBUX', 'AMGN', 'INTU', 'ISRG', 'BKNG',
            
            # Growth stocks
            'ABNB', 'COIN', 'CRWD', 'SNOW', 'DDOG', 'ZS', 'PANW', 'FTNT',
            'DXCM', 'TEAM', 'WDAY', 'MELI', 'SHOP', 'SQ', 'ROKU', 'SPOT',
            
            # Mid caps
            'MRNA', 'LCID', 'RIVN', 'PLTR', 'HOOD', 'RBLX', 'U', 'NET',
            'OKTA', 'DOCU', 'TWLO', 'ZM', 'PTON', 'BYND', 'DASH', 'UBER',
            
            # Semiconductors
            'MU', 'AMAT', 'ADI', 'KLAC', 'MRVL', 'LRCX', 'NXPI', 'SNPS',
            'CDNS', 'MPWR', 'MCHP', 'SWKS', 'QRVO', 'ON', 'STM', 'TSM',
            
            # Biotech
            'GILD', 'VRTX', 'REGN', 'BIIB', 'ILMN', 'ALXN', 'SGEN', 'BMRN',
            
            # Consumer
            'LULU', 'ORLY', 'MAR', 'BKNG', 'PCAR', 'MNST', 'KDP', 'WBA',
            
            # Tech
            'ASML', 'ADP', 'PAYX', 'CTSH', 'ANSS', 'ADSK', 'SPLK', 'VEEV'
        ]
    
    def should_run_selection(self) -> bool:
        """
        Check if we should run stock selection
        Run once per day before market open (6 AM ET)
        """
        current_date = datetime.now().date()
        
        # Already ran today
        if self.last_selection_date == current_date:
            return False
        
        # Run between 6 AM and 9:30 AM ET (before market open)
        current_time = datetime.now().time()
        selection_start = time(6, 0)   # 6:00 AM
        selection_end = time(9, 30)    # 9:30 AM (market open)
        
        # Or run if we never ran before
        if self.last_selection_date is None:
            return True
        
        return selection_start <= current_time < selection_end
    
    def select_daily_stocks(self, min_score: float = 60, top_n: int = 3) -> List[str]:
        """
        Run daily stock selection
        
        Returns:
            List of top N stock symbols
        """
        print(f"\n{'='*80}")
        print(f"📊 DAILY STOCK SELECTION - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*80}")
        print(f"Universe: {len(self.nasdaq_universe)} stocks")
        print(f"Min Score: {min_score}")
        print(f"Target: Top {top_n}")
        print(f"{'='*80}\n")
        
        # Screen all stocks
        scored_stocks = self.scorer.screen_and_rank(
            self.nasdaq_universe,
            min_score=min_score
        )
        
        if not scored_stocks:
            print("⚠️ No stocks met minimum criteria!")
            print("   Falling back to default symbols...")
            return ['AAPL', 'MSFT', 'GOOGL']
        
        # Show all qualifying stocks
        print(f"\n✅ Found {len(scored_stocks)} stocks scoring {min_score}+")
        
        # Select top N with diversification
        top_stocks = self.scorer.select_top_3(scored_stocks) if top_n == 3 else scored_stocks[:top_n]
        
        # Print results
        self.scorer.print_results(top_stocks, f"🏆 TODAY'S TOP {len(top_stocks)} SELECTIONS")
        
        # Update state
        self.current_symbols = [s.symbol for s in top_stocks]
        self.last_selection_date = datetime.now().date()
        
        print(f"\n{'='*80}")
        print(f"✅ SELECTION COMPLETE")
        print(f"   Symbols: {', '.join(self.current_symbols)}")
        print(f"   Valid until: {datetime.now().date()}")
        print(f"{'='*80}\n")
        
        return self.current_symbols
    
    async def auto_select_loop(self, update_callback=None):
        """
        Background task that automatically selects stocks daily
        
        Args:
            update_callback: Function to call when symbols update
        """
        print("🔄 Starting automatic daily stock selection...")
        
        # Run initial selection
        symbols = self.select_daily_stocks()
        if update_callback:
            await update_callback(symbols)
        
        while True:
            try:
                # Check every hour if we should run selection
                await asyncio.sleep(3600)  # 1 hour
                
                if self.should_run_selection():
                    print("\n⏰ Time for daily stock selection...")
                    symbols = self.select_daily_stocks()
                    
                    if update_callback:
                        await update_callback(symbols)
                
            except Exception as e:
                print(f"❌ Error in auto-selection: {e}")
                await asyncio.sleep(3600)  # Wait an hour and try again
    
    def get_current_symbols(self) -> List[str]:
        """Get currently selected symbols"""
        if not self.current_symbols:
            # First run - do selection now
            return self.select_daily_stocks()
        return self.current_symbols
    
    def print_current_selection(self):
        """Print current symbol selection"""
        if not self.current_symbols:
            print("No symbols selected yet")
            return
        
        print(f"\n{'='*80}")
        print(f"📌 CURRENT SELECTION")
        print(f"{'='*80}")
        print(f"Symbols: {', '.join(self.current_symbols)}")
        print(f"Selected: {self.last_selection_date}")
        print(f"Next selection: Tomorrow 6:00 AM ET")
        print(f"{'='*80}\n")


# Standalone script mode
async def run_manual_selection():
    """Run stock selection manually"""
    selector = DailyStockSelector(settings.alpaca_key, settings.alpaca_secret)
    symbols = selector.select_daily_stocks()
    return symbols


if __name__ == "__main__":
    import sys
    
    try:
        symbols = asyncio.run(run_manual_selection())
        print(f"\n💡 To use these symbols in your bot, set:")
        print(f"   SYMBOLS={','.join(symbols)}")
        print(f"\n   Or let main.py auto-select daily.\n")
    except KeyboardInterrupt:
        print("\n\n🛑 Selection cancelled")
        sys.exit(0)