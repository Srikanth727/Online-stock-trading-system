import kagglehub
import pandas as pd
from kagglehub import KaggleDatasetAdapter
from flask import render_template

_stock_data = None


def get_stock_data():
    global _stock_data
    if _stock_data is None:
        _stock_data = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "rohitjain454/all-stocks-5yr",
            "",
        )
        _stock_data['date'] = pd.to_datetime(_stock_data['date'])
    return _stock_data


def lookup(symbol):
    """Look up quote for symbol from local CSV dataset."""
    try:
        df = get_stock_data()
        symbol = symbol.upper()
        stock = df[df['Name'] == symbol]
        if stock.empty:
            return None
        latest = stock.loc[stock['date'].idxmax()]
        return {
            "name": symbol,
            "price": float(latest['close']),
            "symbol": symbol
        }
    except Exception:
        return None


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
