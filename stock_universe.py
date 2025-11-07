"""
Extended Stock Universe
~300 liquid stocks across all sectors for comprehensive screening
"""

# NASDAQ stocks organized by sector
STOCK_UNIVERSE = {
    # Technology - Large Cap
    'mega_tech': [
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'META', 'NVDA', 'AVGO', 'CSCO',
        'ADBE', 'CRM', 'ORCL', 'INTC', 'AMD', 'QCOM', 'TXN', 'AMAT',
        'ADI', 'LRCX', 'KLAC', 'SNPS', 'CDNS', 'MRVL', 'NXPI'
    ],
    
    # Technology - Mid Cap
    'tech_mid': [
        'NOW', 'PANW', 'FTNT', 'CRWD', 'ZS', 'DDOG', 'NET', 'SNOW',
        'MDB', 'TEAM', 'WDAY', 'OKTA', 'ZM', 'DOCU', 'TWLO', 'PLTR',
        'U', 'PATH', 'BILL', 'DKNG', 'COIN', 'HOOD', 'AFRM', 'SOFI'
    ],
    
    # Consumer - E-commerce & Retail
    'consumer': [
        'AMZN', 'TSLA', 'BKNG', 'ABNB', 'EBAY', 'ETSY', 'W', 'CHWY',
        'CVNA', 'RVLV', 'FTCH', 'REAL', 'RH', 'CPRT', 'OLLI', 'FIVE',
        'DLTR', 'DG', 'ROST', 'TJX', 'ULTA', 'LULU', 'NKE', 'DECK'
    ],
    
    # Consumer - Food & Beverage
    'food_bev': [
        'SBUX', 'CMG', 'MCD', 'YUM', 'DPZ', 'QSR', 'WEN', 'JACK',
        'DNKN', 'WING', 'TXRH', 'DRI', 'EAT', 'CAKE', 'BLMN', 'BJRI',
        'PZZA', 'BROS', 'SHAK', 'CAVA', 'CELH', 'MNST', 'PEP', 'KDP'
    ],
    
    # Healthcare - Biotech
    'biotech': [
        'GILD', 'AMGN', 'VRTX', 'REGN', 'BIIB', 'MRNA', 'BNTX', 'ILMN',
        'ALNY', 'INCY', 'SGEN', 'BMRN', 'EXAS', 'TECH', 'IONS', 'UTHR',
        'SRPT', 'RARE', 'FOLD', 'RGNX', 'CRSP', 'NTLA', 'EDIT', 'BEAM'
    ],
    
    # Healthcare - Devices & Services
    'healthcare': [
        'ISRG', 'DXCM', 'ALGN', 'HOLX', 'PODD', 'TDOC', 'VEEV', 'DOCS',
        'HIMS', 'OSCR', 'IRTC', 'NVST', 'NVCR', 'GDRX', 'ACCD', 'OMCL',
        'TMDX', 'TNDM', 'SENS', 'PRVA', 'PCVX', 'ICUI', 'NARI', 'ATRC'
    ],
    
    # Semiconductors
    'semis': [
        'NVDA', 'AMD', 'INTC', 'QCOM', 'AVGO', 'TXN', 'ADI', 'MRVL',
        'NXPI', 'AMAT', 'LRCX', 'KLAC', 'ASML', 'TSM', 'MU', 'WDC',
        'STX', 'SWKS', 'QRVO', 'MPWR', 'MCHP', 'ON', 'WOLF', 'CRUS'
    ],
    
    # Software & Cloud
    'software': [
        'MSFT', 'CRM', 'NOW', 'ADBE', 'ORCL', 'WDAY', 'PANW', 'SNOW',
        'DDOG', 'ZS', 'CRWD', 'FTNT', 'NET', 'MDB', 'TEAM', 'ZM',
        'DOCN', 'ESTC', 'CFLT', 'GTLB', 'S', 'AI', 'PCOR', 'ALTR'
    ],
    
    # Internet & Media
    'internet': [
        'META', 'GOOGL', 'NFLX', 'DIS', 'CMCSA', 'CHTR', 'PARA', 'WBD',
        'SPOT', 'RBLX', 'MTCH', 'BMBL', 'PINS', 'SNAP', 'RDDT', 'YELP',
        'TRIP', 'GRUB', 'DASH', 'UBER', 'LYFT', 'GRAB', 'DIDI', 'CPNG'
    ],
    
    # Automotive & Transport
    'auto': [
        'TSLA', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'FFIE', 'FSR',
        'GOEV', 'RIDE', 'WKHS', 'HYLN', 'BLNK', 'CHPT', 'EVGO', 'QS',
        'LAZR', 'VLDR', 'LIDR', 'OUST', 'INVZ', 'AEYE', 'MBLY', 'APTV'
    ],
    
    # Energy & Clean Tech
    'energy': [
        'ENPH', 'SEDG', 'RUN', 'NOVA', 'ARRY', 'CSIQ', 'JKS', 'FSLR',
        'BE', 'PLUG', 'BLDP', 'FCEL', 'CLNE', 'NEE', 'AEP', 'DUK',
        'CEG', 'VST', 'NRG', 'CWEN', 'AES', 'OKE', 'WMB', 'KMI'
    ],
    
    # Finance & Fintech
    'fintech': [
        'PYPL', 'SQ', 'COIN', 'HOOD', 'SOFI', 'AFRM', 'UPST', 'LC',
        'LMND', 'ROOT', 'MTTR', 'OPEN', 'RVNC', 'LPRO', 'BILL', 'FOUR',
        'STNE', 'PAGS', 'NU', 'MELI', 'PDD', 'BABA', 'JD', 'BIDU'
    ],
    
    # Gaming & Esports
    'gaming': [
        'RBLX', 'EA', 'TTWO', 'ATVI', 'DKNG', 'PENN', 'FLUT', 'CHDN',
        'RSI', 'GENI', 'FUBO', 'MSGS', 'SKLZ', 'SLGG', 'GMBL', 'GNOG',
        'NERD', 'ESPO', 'HERO', 'CONL', 'SBET', 'BETZ', 'LNW', 'EVRI'
    ],
    
    # REITs & Real Estate
    'reits': [
        'EQIX', 'DLR', 'AMT', 'CCI', 'SBAC', 'PLD', 'PSA', 'WELL',
        'AVB', 'EQR', 'INVH', 'MAA', 'CPT', 'UDR', 'ESS', 'AIV',
        'PEAK', 'COLD', 'FR', 'KRC', 'DEI', 'JBGS', 'SLG', 'VNO'
    ],
    
    # Industrial & Manufacturing
    'industrial': [
        'HON', 'CAT', 'DE', 'EMR', 'ETN', 'ITW', 'MMM', 'GE',
        'BA', 'RTX', 'LMT', 'NOC', 'GD', 'TXT', 'HWM', 'CARR',
        'OTIS', 'PCAR', 'FAST', 'ROLL', 'POOL', 'WSO', 'WCC', 'GWW'
    ]
}


def get_full_universe() -> list:
    """Get complete list of all stocks"""
    all_stocks = []
    for sector_stocks in STOCK_UNIVERSE.values():
        all_stocks.extend(sector_stocks)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_stocks = []
    for stock in all_stocks:
        if stock not in seen:
            seen.add(stock)
            unique_stocks.append(stock)
    
    return unique_stocks


def get_sector_universe(sectors: list = None) -> list:
    """Get stocks from specific sectors"""
    if sectors is None:
        return get_full_universe()
    
    selected = []
    for sector in sectors:
        if sector in STOCK_UNIVERSE:
            selected.extend(STOCK_UNIVERSE[sector])
    
    return list(set(selected))


def get_liquid_universe(min_volume: int = 500000) -> list:
    """
    Get most liquid stocks
    For backtesting, we'll use the full universe and filter by volume
    """
    return get_full_universe()


# Quick stats
TOTAL_STOCKS = len(get_full_universe())
SECTORS = list(STOCK_UNIVERSE.keys())

if __name__ == "__main__":
    print(f"Total stocks in universe: {TOTAL_STOCKS}")
    print(f"Sectors: {len(SECTORS)}")
    print(f"\nStocks per sector:")
    for sector, stocks in STOCK_UNIVERSE.items():
        print(f"  {sector}: {len(stocks)} stocks")