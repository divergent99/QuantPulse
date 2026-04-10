<div align="center">

![QuantPulse Banner](assets/banner.jpg)

# QuantPulse

**Algorithmic portfolio risk intelligence, powered by AI**

[![AlgoFest Hackathon 2026](https://img.shields.io/badge/AlgoFest%20Hackathon%202026-Devpost-003E54?style=flat-square&logo=devpost&logoColor=white)](https://devpost.com)
[![Amazon Nova Lite](https://img.shields.io/badge/Amazon-Nova%20Lite-FF9900?style=flat-square&logo=amazonaws&logoColor=white)](https://aws.amazon.com/bedrock)
[![Tavily](https://img.shields.io/badge/Tavily-Live%20Search-4A90E2?style=flat-square)](https://tavily.com)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Plotly Dash](https://img.shields.io/badge/Plotly%20Dash-3.0-3D4CB7?style=flat-square&logo=plotly)](https://dash.plotly.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-1C3C3C?style=flat-square)](https://langchain-ai.github.io/langgraph)

*Enter your portfolio. Get institutional-grade risk analysis in seconds. Ask the AI anything.*

</div>

---

## What it does

Most retail investors know their holdings. They don't know their risk.

QuantPulse runs a full quantitative risk engine on your portfolio — Value at Risk, Sharpe Ratio, Beta, Max Drawdown, Correlation Matrix — then passes the results to a LangGraph agent on Amazon Nova Lite that interprets the numbers in plain English and delivers specific, actionable recommendations. Live market news is fetched via Tavily and matched to your holdings. A context-aware chat lets you ask follow-up questions directly.

**Built for [AlgoFest Hackathon 2026](https://algofest-hackathon26.devpost.com) · Track: FinTech Innovations / AI & ML**

---

## Demo

> ![QuantPulse Demo](assets/demo.jpg)

---

## Stack

| Layer | Tech |
|---|---|
| Agent | LangGraph (`StateGraph` + sequential nodes) |
| LLM | Amazon Nova Lite via AWS Bedrock |
| News | Tavily Search API |
| Market Data | yfinance (real-time) |
| Quant | NumPy · Pandas · SciPy |
| Backend | FastAPI + Uvicorn |
| Frontend | Plotly Dash + Dash Bootstrap Components |
| Deployment | Railway |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/divergent99/quantpulse
cd quantpulse
pip install -r requirements.txt
pip install tavily-python
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS access key with Bedrock permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | AWS region (default: `us-east-1`) |
| `TAVILY_API_KEY` | Tavily API key for live news search |
| `API_URL` | FastAPI base URL (default: `http://localhost:8000`) |

### 3. Run

**Terminal 1 — API:**
```bash
# Windows
$env:PYTHONPATH="src"; uvicorn src.api.main:app --reload --port 8000

# Mac/Linux
PYTHONPATH=src uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 — Dashboard:**
```bash
# Windows
$env:API_URL="http://localhost:8000"; python app.py

# Mac/Linux
API_URL=http://localhost:8000 python app.py
```

Open **http://localhost:8050**

---

## Project Structure

```
quantpulse/
├── app.py                        # Dash frontend + all callbacks
├── start.sh                      # Single-command launch (both services)
├── src/
│   ├── api/
│   │   └── main.py               # FastAPI endpoints
│   ├── analytics/
│   │   ├── engine.py             # Quant engine (VaR, Sharpe, Beta, etc.)
│   │   └── news.py               # Tavily news fetcher
│   └── agents/
│       └── risk_agent.py         # LangGraph agent + Nova Lite calls
├── assets/
│   └── warp.js                   # Three.js star field background
├── .env.example
├── requirements.txt
└── railway.toml
```

---

## Features

**Quant Engine**
- Value at Risk — Historical + Parametric at 95% confidence
- Conditional VaR (Expected Shortfall)
- Sharpe Ratio and Sortino Ratio
- Maximum Drawdown (peak-to-trough)
- Beta vs SPY benchmark
- Risk/Reward Ratio and Tail Risk Ratio
- Diversification Score

**Visualizations (9 charts)**
- Cumulative Returns · Sector Exposure · Correlation Matrix
- VaR Breakdown · Holdings Radar · Return Contribution Waterfall
- Monthly Returns Heatmap · Rolling 30d Volatility · Geographic Revenue Map

**AI Agent**
- Algorithmic risk scoring 0–100
- Plain-English risk narrative
- Sector concentration + correlation risk analysis
- 4 specific actionable recommendations
- Context-aware portfolio chat (ask anything, get number-specific answers)

**Live Intelligence**
- Tavily-powered news — portfolio-specific + macro, tagged and linked

---

## Agent Architecture

```
FastAPI /analyze
       │
yfinance ──► Price Data
       │
Quant Engine (VaR · Sharpe · Beta · Drawdown · Correlation)
       │
LangGraph Agent
  [risk_scorer]          ← algorithmic, no LLM
       ↓
  [risk_narrative]       → Amazon Nova Lite
       ↓
  [sector_analysis]      → Amazon Nova Lite
       ↓
  [correlation_analysis] → Amazon Nova Lite
       ↓
  [generate_recommendations] → Amazon Nova Lite
       │
Tavily News Fetch (parallel)
       │
Dash Dashboard
```

---

## Hackathon

**AlgoFest Hackathon 2026 — Battle of the Beasts** · Devpost
Track: FinTech Innovations + AI & ML
Prize pool: $5,000

---

<div align="center">
Made with Amazon Nova Lite · LangGraph · Tavily · Plotly Dash · yfinance
</div>