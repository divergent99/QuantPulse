from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()


def fetch_portfolio_news(tickers: list, sector_exposure: dict) -> list:
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    top_sectors = sorted(sector_exposure.items(), key=lambda x: x[1], reverse=True)[:2]
    sector_str = " ".join([s[0] for s in top_sectors])
    ticker_str = " ".join(tickers[:4])
    query = f"stock market news {ticker_str} {sector_str} risk outlook 2026"
    results = client.search(query=query, max_results=6, search_depth="basic")
    articles = []
    for r in results.get("results", []):
        articles.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:200],
            "published_date": r.get("published_date", ""),
        })
    return articles


def fetch_macro_news() -> list:
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    results = client.search(query="global macro economic risk market outlook April 2026", max_results=4, search_depth="basic")
    articles = []
    for r in results.get("results", []):
        articles.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:200],
            "published_date": r.get("published_date", ""),
        })
    return articles