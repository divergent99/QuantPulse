from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, END
import os
import json
import boto3


class AgentState(TypedDict):
    analysis_data: Dict[str, Any]
    risk_summary: str
    recommendations: List[str]
    risk_score: int
    risk_label: str
    sector_insights: str
    correlation_insights: str


def invoke_nova(prompt: str) -> str:
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    body = json.dumps({
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"max_new_tokens": 1024, "temperature": 0.3},
    })
    resp = client.invoke_model(
        modelId="amazon.nova-lite-v1:0",
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(resp["body"].read())
    return result["output"]["message"]["content"][0]["text"]


def risk_scorer_node(state: AgentState) -> AgentState:
    metrics = state["analysis_data"]["metrics"]
    score = 50

    sharpe = metrics["sharpe_ratio"]
    if sharpe > 2: score -= 15
    elif sharpe > 1: score -= 8
    elif sharpe < 0: score += 20
    elif sharpe < 0.5: score += 10

    vol = metrics["volatility"]
    if vol > 35: score += 20
    elif vol > 25: score += 10
    elif vol < 10: score -= 10

    dd = abs(metrics["max_drawdown"])
    if dd > 40: score += 15
    elif dd > 25: score += 8
    elif dd < 10: score -= 8

    beta = metrics["beta"]
    if beta > 1.5: score += 10
    elif beta < 0.5: score -= 8

    var = abs(metrics["var_95"]["var_historical"])
    if var > 3: score += 10
    elif var < 1: score -= 5

    score = max(0, min(100, score))

    if score <= 25: label = "Low Risk"
    elif score <= 50: label = "Moderate Risk"
    elif score <= 75: label = "High Risk"
    else: label = "Very High Risk"

    state["risk_score"] = score
    state["risk_label"] = label
    return state


def risk_narrative_node(state: AgentState) -> AgentState:
    metrics = state["analysis_data"]["metrics"]
    tickers = state["analysis_data"]["tickers"]

    prompt = f"""You are a senior portfolio risk analyst. Analyze this portfolio and provide a concise risk summary.

Portfolio: {', '.join(tickers)}
Risk Score: {state['risk_score']}/100 ({state['risk_label']})

Key Metrics:
- Annualized Return: {metrics['annualized_return']}%
- Volatility: {metrics['volatility']}%
- Sharpe Ratio: {metrics['sharpe_ratio']}
- Sortino Ratio: {metrics['sortino_ratio']}
- Max Drawdown: {metrics['max_drawdown']}%
- Beta: {metrics['beta']}
- 95% VaR (Historical): {metrics['var_95']['var_historical']}%
- 95% CVaR: {metrics['var_95']['cvar']}%

Write a 3-4 sentence plain-English risk summary. Be specific about numbers. No fluff."""

    state["risk_summary"] = invoke_nova(prompt)
    return state


def sector_analysis_node(state: AgentState) -> AgentState:
    sector_exp = state["analysis_data"]["sector_exposure"]

    prompt = f"""Analyze this portfolio's sector exposure and identify concentration risks.

Sector Exposure: {json.dumps(sector_exp, indent=2)}

In 2-3 sentences, identify: (1) any over-concentration, (2) diversification gaps, (3) one specific risk this creates.
Be direct and specific."""

    state["sector_insights"] = invoke_nova(prompt)
    return state


def correlation_analysis_node(state: AgentState) -> AgentState:
    corr = state["analysis_data"]["correlation_matrix"]
    tickers = state["analysis_data"]["tickers"]

    high_corr_pairs = []
    for i, t1 in enumerate(tickers):
        for j, t2 in enumerate(tickers):
            if i < j and t1 in corr and t2 in corr.get(t1, {}):
                val = corr[t1][t2]
                if abs(val) > 0.7:
                    high_corr_pairs.append(f"{t1}/{t2}: {val:.2f}")

    prompt = f"""Analyze correlation risk in this portfolio.

Highly correlated pairs (|r| > 0.7): {high_corr_pairs if high_corr_pairs else 'None found'}
Total holdings: {len(tickers)}

In 2 sentences, explain what the correlation structure means for diversification benefit during a market selloff."""

    state["correlation_insights"] = invoke_nova(prompt)
    return state


def recommendations_node(state: AgentState) -> AgentState:
    metrics = state["analysis_data"]["metrics"]
    individual = state["analysis_data"]["individual_metrics"]

    prompt = f"""Based on this portfolio analysis, provide exactly 4 actionable recommendations.

Risk Score: {state['risk_score']}/100 ({state['risk_label']})
Sharpe: {metrics['sharpe_ratio']} | Vol: {metrics['volatility']}% | Max DD: {metrics['max_drawdown']}%
Sector Issues: {state['sector_insights']}
Correlation Issues: {state['correlation_insights']}

Individual holdings:
{json.dumps({k: f"ret={v['annualized_return']}% vol={v['volatility']}% sharpe={v['sharpe']}" for k, v in individual.items()}, indent=2)}

Return ONLY a JSON array of exactly 4 strings, each a specific actionable recommendation under 20 words.
Example: ["Reduce NVDA weight from 30% to 15% to lower single-stock concentration risk"]
No preamble, no explanation, just the JSON array."""

    try:
        content = invoke_nova(prompt).strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        state["recommendations"] = json.loads(content)[:4]
    except Exception:
        state["recommendations"] = [
            "Review concentration in highest-weight positions.",
            "Consider adding uncorrelated asset classes for diversification.",
            "Monitor volatility and rebalance if it exceeds 25% annualized.",
            "Set stop-loss levels based on your max drawdown tolerance.",
        ]
    return state


def build_agent() -> StateGraph:
    workflow = StateGraph(AgentState)
    workflow.add_node("risk_scorer", risk_scorer_node)
    workflow.add_node("risk_narrative", risk_narrative_node)
    workflow.add_node("sector_analysis", sector_analysis_node)
    workflow.add_node("correlation_analysis", correlation_analysis_node)
    workflow.add_node("generate_recommendations", recommendations_node)

    workflow.set_entry_point("risk_scorer")
    workflow.add_edge("risk_scorer", "risk_narrative")
    workflow.add_edge("risk_narrative", "sector_analysis")
    workflow.add_edge("sector_analysis", "correlation_analysis")
    workflow.add_edge("correlation_analysis", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)

    return workflow.compile()


def run_agent(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    agent = build_agent()
    initial_state = AgentState(
        analysis_data=analysis_data,
        risk_summary="",
        recommendations=[],
        risk_score=50,
        risk_label="Moderate Risk",
        sector_insights="",
        correlation_insights="",
    )
    result = agent.invoke(initial_state)
    return {
        "risk_score": result["risk_score"],
        "risk_label": result["risk_label"],
        "risk_summary": result["risk_summary"],
        "sector_insights": result["sector_insights"],
        "correlation_insights": result["correlation_insights"],
        "recommendations": result["recommendations"],
    }