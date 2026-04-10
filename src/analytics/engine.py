import numpy as np
import pandas as pd
import requests
from scipy import stats
from typing import Dict, List
import warnings
import os
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

SECTOR_MAP = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "NVDA": "Technology", "META": "Technology", "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary", "JPM": "Financials", "BAC": "Financials",
    "GS": "Financials", "JNJ": "Healthcare", "PFE": "Healthcare",
    "UNH": "Healthcare", "XOM": "Energy", "CVX": "Energy",
    "WMT": "Consumer Staples", "PG": "Consumer Staples", "KO": "Consumer Staples",
    "SPY": "ETF", "QQQ": "ETF", "VTI": "ETF", "BRK-B": "Financials",
    "V": "Financials", "MA": "Financials", "NFLX": "Technology",
    "AMD": "Technology", "INTC": "Technology", "DIS": "Communication Services",
    "T": "Communication Services", "VZ": "Communication Services",
}

PERIOD_DAYS = {"6mo": 180, "1y": 365, "2y": 730, "5y": 1825}


def fetch_single_ticker(ticker: str, period: str = "1y") -> pd.Series:
    """Fetch price data using multiple fallback sources."""
    days = PERIOD_DAYS.get(period, 365)
    end = datetime.now()
    start = end - timedelta(days=days)

    # Source 1: Alpha Vantage (works from cloud IPs)
    av_key = os.getenv("ALPHA_VANTAGE_KEY", "demo")
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={av_key}"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        print(f"[AV DEBUG] {ticker} response keys: {list(data.keys())}", flush=True)
        if "Note" in data:
            print(f"[AV DEBUG] Rate limit hit: {data['Note']}", flush=True)
        if "Information" in data:
            print(f"[AV DEBUG] Info: {data['Information']}", flush=True)
        if "Time Series (Daily)" in data:
            ts = data["Time Series (Daily)"]
            prices = {}
            for date_str, vals in ts.items():
                date = pd.to_datetime(date_str)
                if start <= date <= end:
                    prices[date] = float(vals["4. close"])
            if len(prices) > 10:
                s = pd.Series(prices).sort_index()
                s.name = ticker
                return s
    except Exception:
        pass

    # Source 2: yfinance with curl_cffi impersonation
    try:
        from curl_cffi import requests as cffi_req
        import yfinance as yf
        session = cffi_req.Session(impersonate="chrome120")
        t = yf.Ticker(ticker, session=session)
        hist = t.history(period=period)
        if len(hist) > 10:
            s = hist["Close"]
            s.name = ticker
            return s
    except Exception:
        pass

    # Source 3: yfinance plain
    try:
        import yfinance as yf
        hist = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        if len(hist) > 10:
            if isinstance(hist.columns, pd.MultiIndex):
                s = hist["Close"][ticker]
            else:
                s = hist["Close"]
            s.name = ticker
            return s
    except Exception:
        pass

    return pd.Series(name=ticker, dtype=float)


def fetch_price_data(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    series = {}
    for t in tickers:
        s = fetch_single_ticker(t, period)
        if len(s) > 10:
            series[t] = s

    if len(series) < 2:
        raise ValueError(
            f"Could not fetch data for enough tickers. "
            f"Got data for: {list(series.keys()) or 'none'}. "
            f"If deploying to cloud, add ALPHA_VANTAGE_KEY env variable."
        )

    df = pd.DataFrame(series)
    df = df.dropna(how="all")
    return df


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()


def compute_portfolio_returns(returns: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    tickers = list(weights.keys())
    available = [t for t in tickers if t in returns.columns]
    w = np.array([weights[t] for t in available])
    r = returns[available].dropna()
    return r.dot(w)


def compute_var(portfolio_returns: pd.Series, confidence: float = 0.95) -> Dict:
    var_historical = np.percentile(portfolio_returns, (1 - confidence) * 100)
    mean = portfolio_returns.mean()
    std = portfolio_returns.std()
    var_parametric = stats.norm.ppf(1 - confidence, mean, std)
    cvar = portfolio_returns[portfolio_returns <= var_historical].mean()
    return {
        "var_historical": round(float(var_historical) * 100, 2),
        "var_parametric": round(float(var_parametric) * 100, 2),
        "cvar": round(float(cvar) * 100, 2),
        "confidence": confidence * 100,
    }


def compute_sharpe(portfolio_returns: pd.Series, risk_free_rate: float = 0.05) -> float:
    daily_rf = risk_free_rate / 252
    excess = portfolio_returns - daily_rf
    sharpe = (excess.mean() / excess.std()) * np.sqrt(252)
    return round(float(sharpe), 2)


def compute_sortino(portfolio_returns: pd.Series, risk_free_rate: float = 0.05) -> float:
    daily_rf = risk_free_rate / 252
    excess = portfolio_returns - daily_rf
    downside = excess[excess < 0].std() * np.sqrt(252)
    sortino = (excess.mean() * 252) / downside if downside != 0 else 0
    return round(float(sortino), 2)


def compute_max_drawdown(portfolio_returns: pd.Series) -> float:
    cumulative = (1 + portfolio_returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    return round(float(drawdown.min()) * 100, 2)


def compute_beta(portfolio_returns: pd.Series, period: str = "1y") -> float:
    try:
        spy = fetch_single_ticker("SPY", period)
        if len(spy) < 10:
            return 1.0
        market_returns = spy.pct_change().dropna()
        aligned = pd.concat([portfolio_returns, market_returns], axis=1).dropna()
        aligned.columns = ["portfolio", "market"]
        cov = aligned.cov().iloc[0, 1]
        var_market = aligned["market"].var()
        return round(float(cov / var_market), 2) if var_market != 0 else 1.0
    except Exception:
        return 1.0


def compute_sector_exposure(weights: Dict[str, float]) -> Dict[str, float]:
    sector_exp = {}
    for ticker, weight in weights.items():
        sector = SECTOR_MAP.get(ticker.upper(), "Other")
        sector_exp[sector] = sector_exp.get(sector, 0) + weight
    return {k: round(v * 100, 2) for k, v in sector_exp.items()}


def compute_annualized_return(portfolio_returns: pd.Series) -> float:
    total = (1 + portfolio_returns).prod()
    n_years = len(portfolio_returns) / 252
    annualized = (total ** (1 / n_years)) - 1 if n_years > 0 else 0
    return round(float(annualized) * 100, 2)


def compute_volatility(portfolio_returns: pd.Series) -> float:
    return round(float(portfolio_returns.std() * np.sqrt(252)) * 100, 2)


def run_full_analysis(tickers: List[str], weights: List[float], period: str = "1y") -> Dict:
    weight_dict = {t: w for t, w in zip(tickers, weights)}

    prices = fetch_price_data(tickers, period)
    available = [t for t in tickers if t in prices.columns]

    raw_weights = {t: weight_dict[t] for t in available}
    total_w = sum(raw_weights.values())
    weight_dict = {t: w / total_w for t, w in raw_weights.items()}

    returns = compute_returns(prices)
    port_returns = compute_portfolio_returns(returns, weight_dict)

    var_metrics = compute_var(port_returns)
    sharpe = compute_sharpe(port_returns)
    sortino = compute_sortino(port_returns)
    max_dd = compute_max_drawdown(port_returns)
    beta = compute_beta(port_returns, period)
    sector_exp = compute_sector_exposure(weight_dict)
    ann_return = compute_annualized_return(port_returns)
    volatility = compute_volatility(port_returns)
    corr_matrix = returns[available].corr().round(2)

    cumulative_returns = (1 + port_returns).cumprod()
    cumulative_returns.index = cumulative_returns.index.strftime("%Y-%m-%d")

    individual_metrics = {}
    for ticker in available:
        t_returns = returns[ticker].dropna()
        individual_metrics[ticker] = {
            "annualized_return": round(float(((1 + t_returns).prod() ** (252 / len(t_returns))) - 1) * 100, 2),
            "volatility": round(float(t_returns.std() * np.sqrt(252)) * 100, 2),
            "sharpe": round(float((t_returns.mean() / t_returns.std()) * np.sqrt(252)), 2),
            "weight": round(weight_dict[ticker] * 100, 2),
        }

    return {
        "tickers": available,
        "weights": weight_dict,
        "metrics": {
            "annualized_return": ann_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": max_dd,
            "beta": beta,
            "var_95": var_metrics,
        },
        "sector_exposure": sector_exp,
        "correlation_matrix": corr_matrix.to_dict(),
        "cumulative_returns": cumulative_returns.to_dict(),
        "individual_metrics": individual_metrics,
    }