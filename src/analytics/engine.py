import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
from typing import Dict, List, Tuple
import warnings
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


def fetch_price_data(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    # Set headers to bypass Yahoo Finance datacenter IP blocks
    import yfinance as yf
    yf.utils.get_json = lambda url, proxy=None, timeout=None: {}
    session = None
    try:
        import requests as req_lib
        session = req_lib.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
    except Exception:
        pass
    data = yf.download(tickers, period=period, auto_adjust=True, progress=False, session=session)
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        prices = data[["Close"]] if "Close" in data.columns else data
    # Drop columns that are entirely NaN (failed/invalid tickers)
    prices = prices.dropna(axis=1, how="all")
    prices = prices.dropna(how="all")
    if prices.empty or len(prices) < 10:
        raise ValueError("Could not fetch price data. Check your ticker symbols are valid (e.g. AAPL, MSFT).")
    return prices


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()


def compute_portfolio_returns(returns: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    tickers = list(weights.keys())
    w = np.array([weights[t] for t in tickers])
    r = returns[tickers].dropna()
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


def compute_correlation_matrix(returns: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
    return returns[tickers].corr().round(3)


def compute_beta(portfolio_returns: pd.Series, market_ticker: str = "SPY", period: str = "1y") -> float:
    try:
        market_data = yf.download(market_ticker, period=period, auto_adjust=True, progress=False)
        market_returns = market_data["Close"].pct_change().dropna()
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
    if len(available) < 2:
        raise ValueError("Need at least 2 valid tickers. Check your symbols (e.g. AAPL, MSFT, NVDA).")
    # Reweight to only available tickers
    raw_weights = {t: weight_dict[t] for t in available}
    total_w = sum(raw_weights.values())
    weight_dict = {t: w / total_w for t, w in raw_weights.items()}

    returns = compute_returns(prices)
    port_returns = compute_portfolio_returns(returns, weight_dict)

    var_metrics = compute_var(port_returns)
    sharpe = compute_sharpe(port_returns)
    sortino = compute_sortino(port_returns)
    max_dd = compute_max_drawdown(port_returns)
    beta = compute_beta(port_returns)
    sector_exp = compute_sector_exposure(weight_dict)
    ann_return = compute_annualized_return(port_returns)
    volatility = compute_volatility(port_returns)
    corr_matrix = compute_correlation_matrix(returns, available)

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