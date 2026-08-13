import yfinance as yf
import json
import sys

def analyze(ticker):
    stock = yf.Ticker(ticker)
    
    try:
        info = stock.info
        name = info.get('shortName', ticker)
        price = info.get('currentPrice', 0)
        roe = info.get('returnOnEquity', 'N/A')
        roa = info.get('returnOnAssets', 'N/A')
        ebitda = info.get('ebitda', 'N/A')
        margins = info.get('profitMargins', 'N/A')
        debt_to_equity = info.get('debtToEquity', 'N/A')
        fcf = info.get('freeCashflow', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        
        print(json.dumps({
            "ticker": ticker,
            "name": name,
            "price": price,
            "metrics": {
                "ROE": f"{roe:.2%}" if isinstance(roe, (int, float)) else roe,
                "ROA": f"{roa:.2%}" if isinstance(roa, (int, float)) else roa,
                "Profit_Margin": f"{margins:.2%}" if isinstance(margins, (int, float)) else margins,
                "EBITDA": ebitda,
                "Free_Cash_Flow": fcf,
                "Debt_to_Equity": debt_to_equity,
                "P/E Ratio": pe_ratio
            }
        }, indent=2))
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "NVDA"]
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    
    for t in tickers:
        analyze(t)
