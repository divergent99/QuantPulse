from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analytics.engine import run_full_analysis
from analytics.news import fetch_portfolio_news, fetch_macro_news
from agents.risk_agent import run_agent

app = FastAPI(title="QuantPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PortfolioRequest(BaseModel):
    tickers: List[str]
    weights: List[float]
    period: str = "1y"

    @validator("weights")
    def normalize_weights(cls, v):
        total = sum(v)
        if total == 0:
            raise ValueError("Weights cannot all be zero")
        return [w / total for w in v]

    @validator("tickers")
    def validate_tickers(cls, v):
        if len(v) == 0:
            raise ValueError("At least one ticker required")
        if len(v) > 10:
            raise ValueError("Maximum 10 tickers allowed")
        return [t.upper().strip() for t in v]


@app.get("/health")
def health():
    return {"status": "ok", "service": "QuantPulse"}


@app.post("/analyze")
def analyze_portfolio(request: PortfolioRequest) -> Dict[str, Any]:
    if len(request.tickers) != len(request.weights):
        raise HTTPException(status_code=400, detail="Tickers and weights length mismatch")
    try:
        analysis = run_full_analysis(request.tickers, request.weights, request.period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    try:
        agent_output = run_agent(analysis)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")

    try:
        news = fetch_portfolio_news(analysis["tickers"], analysis["sector_exposure"])
        macro = fetch_macro_news()
    except Exception:
        news = []
        macro = []
    return {**analysis, "ai_insights": agent_output, "news": news, "macro_news": macro}