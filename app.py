import dash
from dash import dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
import json
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    external_scripts=["https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"],
    title="QuantPulse",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

RISK_COLORS = {"Low Risk":"#00e5a0","Moderate Risk":"#f5c542","High Risk":"#ff7043","Very High Risk":"#ff1744"}
PRESETS = {
    "Tech Heavy":        {"tickers":["AAPL","MSFT","NVDA","GOOGL","META"], "weights":[25,25,20,15,15]},
    "Balanced":          {"tickers":["AAPL","JPM","JNJ","XOM","WMT"],      "weights":[20,20,20,20,20]},
    "Aggressive Growth": {"tickers":["NVDA","TSLA","AMD","META","AMZN"],   "weights":[30,25,20,15,10]},
}
CHART_COLORS = ["#00d4ff","#7c4dff","#00e5a0","#f5c542","#ff7043","#ff4081","#40c4ff","#ffab40","#ea80fc","#b2ff59"]
GEO_MAP = {
    "AAPL":{"United States":43,"China":19,"Europe":24,"Rest of World":14},
    "MSFT":{"United States":50,"Europe":28,"Asia":15,"Rest of World":7},
    "NVDA":{"United States":40,"China":17,"Taiwan":8,"Europe":20,"Rest of World":15},
    "GOOGL":{"United States":47,"Europe":30,"Asia":15,"Rest of World":8},
    "META":{"United States":45,"Europe":27,"Asia":18,"Rest of World":10},
    "AMZN":{"United States":62,"Europe":25,"Rest of World":13},
    "TSLA":{"United States":47,"China":22,"Europe":23,"Rest of World":8},
    "JPM":{"United States":65,"Europe":20,"Rest of World":15},
    "JNJ":{"United States":50,"Europe":25,"Asia":15,"Rest of World":10},
    "XOM":{"United States":40,"Europe":15,"Asia":25,"Rest of World":20},
    "WMT":{"United States":70,"China":5,"Mexico":6,"Rest of World":19},
    "AMD":{"United States":35,"China":22,"Taiwan":10,"Europe":18,"Rest of World":15},
}
COUNTRY_ISO = {"United States":"USA","China":"CHN","Europe":"FRA","Asia":"JPN","Taiwan":"TWN","Mexico":"MEX","Rest of World":"BRA"}

app.index_string = '''<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#0d1117;color:#e6edf3;font-family:"Space Grotesk",sans-serif;overflow-x:hidden}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:#0d1117}::-webkit-scrollbar-thumb{background:#21262d;border-radius:2px}
#root{position:relative;z-index:2}
#qp-wrap{display:grid;grid-template-columns:260px 1fr 300px;min-height:100vh}

/* SIDEBAR */
#qp-side{background:#161b22;border-right:1px solid #21262d;display:flex;flex-direction:column;height:100vh;position:sticky;top:0}
.side-top{padding:18px 16px 14px;border-bottom:1px solid #21262d;display:flex;align-items:center;gap:10px}
.logo-mark{width:30px;height:30px;background:linear-gradient(135deg,#00d4ff,#7c4dff);border-radius:7px;display:flex;align-items:center;justify-content:center;font-family:"JetBrains Mono",monospace;font-size:10px;font-weight:700;color:#0d1117;flex-shrink:0}
.logo-text{font-size:15px;font-weight:700;color:#e6edf3}
.logo-text span{color:#00d4ff}
.side-scroll{flex:1;overflow-y:auto;padding:12px 14px}
.s-lbl{font-family:"JetBrains Mono",monospace;font-size:9px;color:#484f58;letter-spacing:2px;text-transform:uppercase;margin:14px 0 7px}
.s-lbl:first-child{margin-top:0}
.preset-row{display:flex;flex-wrap:wrap;gap:4px}
.p-btn{background:transparent!important;border:1px solid #21262d!important;color:#484f58!important;font-family:"JetBrains Mono",monospace!important;font-size:9px!important;padding:4px 9px!important;border-radius:5px!important;transition:all 0.15s!important}
.p-btn:hover{border-color:rgba(0,212,255,0.4)!important;color:#00d4ff!important;background:rgba(0,212,255,0.05)!important}
.t-grid{display:grid;grid-template-columns:1fr 58px;gap:4px;margin-bottom:4px}
.qin{background:#0d1117!important;border:1px solid #21262d!important;border-radius:5px!important;color:#c9d1d9!important;font-family:"JetBrains Mono",monospace!important;font-size:11px!important;padding:6px 8px!important;width:100%!important;transition:all 0.15s!important}
.qin:focus{border-color:rgba(0,212,255,0.4)!important;outline:none!important;box-shadow:0 0 0 2px rgba(0,212,255,0.08)!important}
.qin::placeholder{color:#30363d!important}
.side-foot{padding:11px 14px 15px;border-top:1px solid #21262d}
.run-btn{width:100%;background:linear-gradient(135deg,rgba(0,212,255,0.1),rgba(124,77,255,0.1))!important;border:1px solid rgba(0,212,255,0.25)!important;border-radius:7px!important;color:#00d4ff!important;font-family:"Space Grotesk",sans-serif!important;font-weight:600!important;font-size:13px!important;padding:11px!important;transition:all 0.2s!important}
.run-btn:hover{background:linear-gradient(135deg,rgba(0,212,255,0.18),rgba(124,77,255,0.18))!important;border-color:rgba(0,212,255,0.5)!important;box-shadow:0 0 20px rgba(0,212,255,0.12)!important}
.err{font-family:"JetBrains Mono",monospace;font-size:9px;color:#f85149;margin-top:7px;line-height:1.5}

/* PERIOD */
.period-wrap{display:flex;gap:4px}
.period-wrap label{background:transparent;border:1px solid #21262d;color:#484f58;font-family:"JetBrains Mono",monospace;font-size:9px;padding:5px 11px;border-radius:5px;cursor:pointer;transition:all 0.15s;display:inline-block}
.period-wrap label:hover{border-color:rgba(0,212,255,0.35);color:#58a6ff}
.period-wrap input[type=radio]{display:none}
.period-wrap input[type=radio]:checked + label{border-color:rgba(0,212,255,0.5);color:#00d4ff;background:rgba(0,212,255,0.06)}

/* MAIN */
#qp-main{padding:18px 20px;overflow-y:auto;height:100vh}
.topbar{display:flex;align-items:center;gap:10px;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid #21262d}
.live-dot{width:6px;height:6px;border-radius:50%;background:#00e5a0;flex-shrink:0;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(0,229,160,0.4)}50%{box-shadow:0 0 0 5px rgba(0,229,160,0)}}
.topbar-title{font-family:"JetBrains Mono",monospace;font-size:10px;color:#58a6ff;letter-spacing:1px}
.topbar-line{flex:1;height:1px;background:linear-gradient(90deg,#21262d,transparent)}
.topbar-time{font-family:"JetBrains Mono",monospace;font-size:10px;color:#484f58}

/* METRIC CARDS */
.m-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}
.m-card{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px 14px;position:relative;overflow:hidden;transition:all 0.2s}
.m-card:hover{border-color:rgba(0,212,255,0.2);transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.4)}
.m-card::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,rgba(0,212,255,0.25),transparent)}
.m-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.m-lbl{font-family:"JetBrains Mono",monospace;font-size:8px;color:#484f58;letter-spacing:1.5px;text-transform:uppercase}
.m-badge{font-family:"JetBrains Mono",monospace;font-size:8px;color:#8b949e;background:#21262d;border-radius:3px;padding:2px 6px;letter-spacing:0.5px;border:1px solid #30363d}
.m-val{font-size:24px;font-weight:700;line-height:1;letter-spacing:-0.5px;font-variant-numeric:tabular-nums}
.m-sub{font-size:10px;color:#484f58;margin-top:5px}

/* SECTION */
.sh{display:flex;align-items:center;gap:8px;margin-bottom:12px}
.sh-txt{font-family:"JetBrains Mono",monospace;font-size:9px;color:#484f58;letter-spacing:2px;white-space:nowrap;text-transform:uppercase}
.sh-line{flex:1;height:1px;background:linear-gradient(90deg,#21262d,transparent)}

/* PANELS */
.qp{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:18px;margin-bottom:12px}

/* RISK */
.risk-panel{display:flex;flex-direction:column;gap:20px}
.risk-gauge-wrap{display:flex;align-items:center;gap:24px;padding-bottom:20px;border-bottom:1px solid #21262d}
.risk-label{font-weight:700;font-size:13px;letter-spacing:1px;font-family:"JetBrains Mono",monospace;text-transform:uppercase}
.ai-sub{font-family:"JetBrains Mono",monospace;font-size:9px;color:#484f58;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;margin-top:18px;padding-bottom:4px;border-bottom:1px solid #21262d}
.ai-sub:first-child{margin-top:0;padding-bottom:4px;border-bottom:1px solid #21262d}
.ai-txt{font-size:14px;color:#8b949e;line-height:1.75;font-weight:300}

/* RECS */
.rec-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.rec-card{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:12px;display:flex;gap:10px;align-items:flex-start;transition:border-color 0.15s}
.rec-card:hover{border-color:rgba(0,212,255,0.2)}
.rec-n{font-family:"JetBrains Mono",monospace;font-size:10px;color:#00d4ff;background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.18);border-radius:5px;width:24px;height:24px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.rec-t{font-size:12px;color:#8b949e;line-height:1.5}

/* TABLE */
.q-tbl{width:100%;border-collapse:collapse}
.q-tbl th{font-family:"JetBrains Mono",monospace;font-size:8px;color:#484f58;letter-spacing:1.5px;text-transform:uppercase;font-weight:400;padding:7px 12px;border-bottom:1px solid #21262d;text-align:left}
.q-tbl td{font-size:13px;padding:10px 12px;border-bottom:1px solid rgba(33,38,45,0.5);color:#8b949e}
.q-tbl tr:last-child td{border-bottom:none}
.q-tbl tbody tr:hover td{background:rgba(0,212,255,0.02)}
.tc{font-family:"JetBrains Mono",monospace;font-size:11px;color:#58a6ff;font-weight:600}

/* NEWS */
.news-item{padding:10px 0;border-bottom:1px solid #21262d}
.news-item:last-child{border-bottom:none;padding-bottom:0}
.news-tag{font-family:"JetBrains Mono",monospace;font-size:8px;padding:2px 6px;border-radius:3px;margin-bottom:5px;display:inline-block;letter-spacing:1px}
.news-title{font-size:13px;color:#c9d1d9;line-height:1.4;font-weight:500;text-decoration:none;display:block;margin-bottom:3px;transition:color 0.15s}
.news-title:hover{color:#58a6ff}
.news-snippet{font-size:11px;color:#484f58;line-height:1.5}

/* LOADING */
.loading-wrap{display:flex;flex-direction:column;align-items:center;justify-content:center;height:55vh;gap:16px}
.loading-ring{width:44px;height:44px;border:2px solid #21262d;border-top-color:#00d4ff;border-radius:50%;animation:spin 0.8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-txt{font-family:"JetBrains Mono",monospace;font-size:10px;color:#484f58;letter-spacing:2px}
.loading-steps{display:flex;flex-direction:column;gap:5px;align-items:flex-start}
.loading-step{font-family:"JetBrains Mono",monospace;font-size:9px;color:#30363d;letter-spacing:1px}
.loading-step.on{color:#00d4ff}

/* EMPTY */
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:55vh;gap:10px}
.e-icon{font-family:"JetBrains Mono",monospace;font-size:24px;color:#21262d;letter-spacing:4px}
.e-txt{font-family:"JetBrains Mono",monospace;font-size:10px;color:#30363d;letter-spacing:2px}
.e-sub{font-family:"JetBrains Mono",monospace;font-size:9px;color:#21262d;letter-spacing:1px}

/* CHAT */
#qp-chat{background:#161b22;border-left:1px solid #21262d;display:flex;flex-direction:column;height:100vh;position:sticky;top:0}
.chat-top{padding:15px 14px 12px;border-bottom:1px solid #21262d}
.chat-title{font-size:14px;font-weight:600;color:#e6edf3}
.chat-sub{font-family:"JetBrains Mono",monospace;font-size:8px;color:#484f58;letter-spacing:1px;margin-top:2px}
.chat-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:10px}
.bw-user{display:flex;justify-content:flex-end}
.bw-bot{display:flex;justify-content:flex-start;align-items:flex-start;gap:8px}
.bot-av{width:28px;height:28px;border-radius:7px;background:linear-gradient(135deg,rgba(0,212,255,0.12),rgba(124,77,255,0.12));border:1px solid rgba(0,212,255,0.18);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-family:"JetBrains Mono",monospace;font-size:9px;color:#00d4ff;margin-top:2px}
.b-user{background:linear-gradient(135deg,rgba(0,212,255,0.12),rgba(124,77,255,0.08));border:1px solid rgba(0,212,255,0.18);border-radius:14px 14px 3px 14px;padding:9px 13px;font-size:12px;color:#c9d1d9;max-width:88%;line-height:1.5}
.b-bot{background:#0d1117;border:1px solid #21262d;border-radius:3px 14px 14px 14px;padding:11px 13px;font-size:13px;color:#8b949e;max-width:93%;line-height:1.65}
.b-lbl{font-family:"JetBrains Mono",monospace;font-size:7px;color:#484f58;letter-spacing:1.5px;margin-bottom:5px;text-transform:uppercase}
.typing{display:flex;gap:4px;align-items:center;padding:2px 0}
.typing span{width:5px;height:5px;border-radius:50%;background:#58a6ff;opacity:0.3;animation:td 1.2s ease-in-out infinite}
.typing span:nth-child(2){animation-delay:0.2s}
.typing span:nth-child(3){animation-delay:0.4s}
@keyframes td{0%,60%,100%{transform:translateY(0);opacity:0.3}30%{transform:translateY(-4px);opacity:0.9}}
.chat-foot{padding:10px 12px 14px;border-top:1px solid #21262d}
.chat-inp-row{display:flex;gap:6px;align-items:center}
.chat-inp{flex:1;background:#0d1117!important;border:1px solid #21262d!important;border-radius:20px!important;color:#c9d1d9!important;font-family:"Space Grotesk",sans-serif!important;font-size:12px!important;padding:9px 14px!important;transition:all 0.15s!important}
.chat-inp:focus{border-color:rgba(0,212,255,0.35)!important;outline:none!important}
.chat-inp::placeholder{color:#30363d!important}
.send-btn{background:rgba(0,212,255,0.1)!important;border:1px solid rgba(0,212,255,0.22)!important;color:#00d4ff!important;font-size:16px!important;width:36px!important;height:36px!important;border-radius:50%!important;padding:0!important;transition:all 0.15s!important;flex-shrink:0!important}
.send-btn:hover{background:rgba(0,212,255,0.18)!important;border-color:#00d4ff!important}
.chat-hints{display:flex;flex-wrap:wrap;gap:4px;margin-top:7px}
.h-chip{font-size:10px;color:#484f58;border:1px solid #21262d;border-radius:10px;padding:3px 9px;cursor:pointer;transition:all 0.15s;background:transparent}
.h-chip:hover{border-color:rgba(0,212,255,0.25);color:#8b949e}

.fi{opacity:0;transform:translateY(6px);animation:fi 0.3s ease forwards}
.d1{animation-delay:0.03s}.d2{animation-delay:0.07s}.d3{animation-delay:0.11s}.d4{animation-delay:0.15s}.d5{animation-delay:0.19s}.d6{animation-delay:0.23s}.d7{animation-delay:0.27s}.d8{animation-delay:0.31s}.d9{animation-delay:0.35s}.d10{animation-delay:0.39s}
@keyframes fi{to{opacity:1;transform:none}}
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}
<script>
setInterval(function(){
    var labels = document.querySelectorAll("#period-store label");
    labels.forEach(function(lbl){
        var inp = lbl.previousElementSibling;
        if(inp && inp.checked){
            lbl.style.borderColor="rgba(0,212,255,0.5)";
            lbl.style.color="#00d4ff";
            lbl.style.background="rgba(0,212,255,0.07)";
        } else {
            lbl.style.borderColor="#21262d";
            lbl.style.color="#484f58";
            lbl.style.background="transparent";
        }
    });
}, 150);
</script></footer>
</body>
</html>'''


def ticker_row(i):
    return html.Div([
        dbc.Input(id={"type":"ticker","index":i}, placeholder="AAPL", className="qin"),
        dbc.Input(id={"type":"weight","index":i}, placeholder="wt%", type="number", min=0, max=100, className="qin"),
    ], className="t-grid")

def sh(txt):
    return html.Div([html.Span(txt,className="sh-txt"),html.Div(className="sh-line")],className="sh")

def fmt(v,d=2):
    try: return round(float(v),d)
    except: return v


def period_selector():
    return dcc.RadioItems(
        id="period-store",
        options=[{"label":l,"value":v} for l,v in [("6M","6mo"),("1Y","1y")]],
        value="1y",
        inline=True,
        inputStyle={"display":"none"},
        labelStyle={
            "fontFamily":"JetBrains Mono,monospace","fontSize":"9px",
            "padding":"5px 11px","borderRadius":"5px","cursor":"pointer",
            "border":"1px solid #21262d","color":"#484f58",
            "marginRight":"4px","display":"inline-block","transition":"all 0.15s",
        },
    )


sidebar = html.Div([
    html.Div([
        html.Div("QP", className="logo-mark"),
        html.Div([html.Span("Quant"),html.Span("Pulse",style={"color":"#00d4ff"})], className="logo-text"),
    ], className="side-top"),
    html.Div([
        html.Div("Presets", className="s-lbl"),
        html.Div([dbc.Button(n,id={"type":"preset","index":n},className="p-btn") for n in PRESETS], className="preset-row"),
        html.Div("Holdings", className="s-lbl"),
        html.Div([ticker_row(i) for i in range(8)]),
        html.Div("Period", className="s-lbl"),
        period_selector(),
        dcc.Store(id="portfolio-store", data={}),
        dcc.Store(id="chat-store", data=[]),
    ], className="side-scroll"),
    html.Div([
        dbc.Button("Run Analysis", id="analyze-btn", className="run-btn"),
        html.Div(id="err-msg", className="err"),
    ], className="side-foot"),
], id="qp-side")


chat_panel = html.Div([
    html.Div([
        html.Div("Portfolio Chat", className="chat-title"),
        html.Div("Powered by Amazon Nova", className="chat-sub"),
    ], className="chat-top"),
    html.Div(id="chat-messages", children=[
        html.Div([
            html.Div("AI", className="bot-av"),
            html.Div([html.Div("NOVA", className="b-lbl"),
                      "Run an analysis first, then ask me anything about your portfolio."],
                     className="b-bot"),
        ], className="bw-bot"),
    ], className="chat-msgs"),
    html.Div([
        html.Div([
            dbc.Input(id="chat-input", placeholder="Ask about your portfolio...", className="chat-inp"),
            dbc.Button("↑", id="chat-send", className="send-btn"),
        ], className="chat-inp-row"),
        html.Div([
            html.Span("Why is my Sharpe low?", id="hint-1", className="h-chip"),
            html.Span("Reduce beta", id="hint-2", className="h-chip"),
            html.Span("Overexposed?", id="hint-3", className="h-chip"),
            html.Span("Rebalancing tips", id="hint-4", className="h-chip"),
        ], className="chat-hints"),
    ], className="chat-foot"),
], id="qp-chat")


app.layout = html.Div([
    sidebar,
    html.Div([
        html.Div([
            html.Div(className="live-dot"),
            html.Span("QuantPulse — Risk Dashboard", className="topbar-title"),
            html.Div(className="topbar-line"),
            html.Span(id="clock", style={"fontFamily":"JetBrains Mono,monospace","fontSize":"10px","color":"#484f58"}),
            dcc.Interval(id="clock-iv", interval=1000),
        ], className="topbar"),
        html.Div(id="loading-screen", style={"display":"none"}, children=[
            html.Div([
                html.Div(className="loading-ring"),
                html.Div("ANALYZING PORTFOLIO", className="loading-txt"),
                html.Div([
                    html.Div("→ Fetching market data", className="loading-step on"),
                    html.Div("→ Running quant engine", className="loading-step"),
                    html.Div("→ AI risk assessment", className="loading-step"),
                    html.Div("→ Fetching news", className="loading-step"),
                ], className="loading-steps"),
            ], className="loading-wrap"),
        ]),
        html.Div(id="results", children=[
            html.Div([
                html.Div("[ ]", className="e-icon"),
                html.Div("NO PORTFOLIO LOADED", className="e-txt"),
                html.Div("Select a preset or enter tickers to begin", className="e-sub"),
            ], className="empty")
        ]),
    ], id="qp-main"),
    chat_panel,
], id="qp-wrap")


# JS to handle period radio + loading screen toggle
app.clientside_callback(
    """
    function(n) {
        if (!n) return window.dash_clientside.no_update;
        var ls = document.getElementById('loading-screen');
        var rs = document.getElementById('results');
        if (ls) ls.style.display = 'block';
        if (rs) rs.style.display = 'none';
        return window.dash_clientside.no_update;
    }
    """,
    Output("results", "style", allow_duplicate=True),
    Input("analyze-btn", "n_clicks"),
    prevent_initial_call=True,
)

# Hide loading when results update
app.clientside_callback(
    """
    function(children) {
        var ls = document.getElementById('loading-screen');
        var rs = document.getElementById('results');
        if (ls) ls.style.display = 'none';
        if (rs) rs.style.display = 'block';
        return window.dash_clientside.no_update;
    }
    """,
    Output("results", "style", allow_duplicate=True),
    Input("results", "children"),
    prevent_initial_call=True,
)


@app.callback(Output("clock","children"), Input("clock-iv","n_intervals"))
def tick(_):
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")


@app.callback(
    [Output({"type":"ticker","index":i},"value") for i in range(8)] +
    [Output({"type":"weight","index":i},"value") for i in range(8)],
    [Input({"type":"preset","index":n},"n_clicks") for n in PRESETS],
    prevent_initial_call=True,
)
def load_preset(*_):
    ctx=dash.callback_context
    if not ctx.triggered: return [no_update]*16
    name=json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["index"]
    p=PRESETS[name]
    return p["tickers"]+[""]*(8-len(p["tickers"]))+p["weights"]+[None]*(8-len(p["weights"]))


def mk_gauge(score,label):
    color=RISK_COLORS.get(label,"#f5c542")
    fig=go.Figure(go.Indicator(
        mode="gauge+number",value=score,
        gauge={"axis":{"range":[0,100],"tickcolor":"#21262d","tickfont":{"color":"#484f58","size":8}},"bar":{"color":color,"thickness":0.5},"bgcolor":"#0d1117","bordercolor":"#21262d","borderwidth":1,
               "steps":[{"range":[0,25],"color":"rgba(0,229,160,0.04)"},{"range":[25,50],"color":"rgba(245,197,66,0.04)"},{"range":[50,75],"color":"rgba(255,112,67,0.04)"},{"range":[75,100],"color":"rgba(248,81,73,0.04)"}]},
        number={"font":{"color":color,"size":32,"family":"JetBrains Mono"}},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=10,b=0,l=10,r=10),height=155)
    return fig


def bc(h=200):
    return dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=6,b=26,l=36,r=6),height=h,
                font={"color":"#484f58","family":"JetBrains Mono","size":9},
                xaxis={"gridcolor":"#161b22","tickfont":{"size":9},"zeroline":False,"showline":False},
                yaxis={"gridcolor":"#161b22","tickfont":{"size":9},"zeroline":False,"showline":False},showlegend=False)


def build_geo(tickers,weights):
    exp={}
    for t,w in zip(tickers,weights):
        for c,p in GEO_MAP.get(t,{"United States":100}).items():
            exp[c]=exp.get(c,0)+(p*w)
    total=sum(exp.values())
    if total>0: exp={k:round(v/total*100,1) for k,v in exp.items()}
    fig=go.Figure(go.Choropleth(
        locations=[COUNTRY_ISO.get(c,"USA") for c in exp],z=list(exp.values()),
        text=[f"{c}: {v:.1f}%" for c,v in exp.items()],hovertemplate="%{text}<extra></extra>",
        colorscale=[[0,"#0d1117"],[0.35,"#0a2540"],[0.7,"#0a4070"],[1,"#00d4ff"]],showscale=False,
        marker_line_color="rgba(0,212,255,0.1)",marker_line_width=0.5))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",margin=dict(t=0,b=0,l=0,r=0),height=200,
        geo=dict(bgcolor="rgba(0,0,0,0)",showframe=False,showcoastlines=True,
                 coastlinecolor="rgba(0,212,255,0.1)",showland=True,landcolor="#161b22",
                 showocean=True,oceancolor="#0d1117",showcountries=True,
                 countrycolor="rgba(255,255,255,0.04)",projection_type="natural earth"))
    return fig


def build_var_chart(var_hist,var_param,cvar):
    fig=go.Figure()
    cats=["Hist. VaR","Param. VaR","CVaR"]
    vals=[abs(var_hist),abs(var_param),abs(cvar)]
    colors=["#00d4ff","#7c4dff","#ff4d6d"]
    fig.add_trace(go.Bar(x=cats,y=vals,marker_color=colors,marker_line_width=0,
        text=[f"{v:.2f}%" for v in vals],textposition="outside",
        textfont={"color":"#8b949e","size":10,"family":"JetBrains Mono"}))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20,b=24,l=36,r=6),height=200,bargap=0.35,
        font={"color":"#484f58","family":"JetBrains Mono","size":9},showlegend=False,
        xaxis={"gridcolor":"#161b22","tickfont":{"size":9},"zeroline":False,"showline":False},
        yaxis={"ticksuffix":"%","gridcolor":"#161b22","tickfont":{"size":8},"zeroline":False})
    return fig


def build_returns_dist(port_returns_dict):
    """Monthly returns heatmap"""
    try:
        s=pd.Series(port_returns_dict)
        s.index=pd.to_datetime(s.index)
        monthly=s.resample("ME").apply(lambda x:(1+x).prod()-1)*100
        df=pd.DataFrame({"year":monthly.index.year,"month":monthly.index.month,"ret":monthly.values})
        pivot=df.pivot(index="year",columns="month",values="ret")
        month_names=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        cols=[month_names[c-1] for c in pivot.columns]
        fig=go.Figure(go.Heatmap(
            z=pivot.values,x=cols,y=pivot.index.astype(str),
            colorscale=[[0,"#ff4d6d"],[0.5,"#161b22"],[1,"#00e5a0"]],
            zmid=0,text=[[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in pivot.values],
            texttemplate="%{text}",textfont={"size":8,"family":"JetBrains Mono"},showscale=False,
            hovertemplate="<b>%{y} %{x}</b>: %{z:.2f}%<extra></extra>"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=6,b=30,l=40,r=6),height=220,
            xaxis={"tickfont":{"size":9,"color":"#8b949e"}},yaxis={"tickfont":{"size":9,"color":"#8b949e"}})
        return fig
    except:
        return None


def build_waterfall(individual_metrics):
    """Contribution waterfall"""
    tickers=list(individual_metrics.keys())
    contribs=[individual_metrics[t]["annualized_return"]*individual_metrics[t]["weight"]/100 for t in tickers]
    total=sum(contribs)
    measures=["relative"]*len(tickers)+["total"]
    x=tickers+["Portfolio"]
    y=contribs+[total]
    fig=go.Figure(go.Waterfall(
        x=x,y=y,measure=measures,
        connector={"line":{"color":"rgba(0,212,255,0.15)","width":1}},
        decreasing={"marker":{"color":"#ff4d6d","line":{"width":0}}},
        increasing={"marker":{"color":"#00e5a0","line":{"width":0}}},
        totals={"marker":{"color":"#00d4ff","line":{"width":0}}},
        text=[f"{v:.2f}%" for v in y],textfont={"size":9,"family":"JetBrains Mono","color":"#8b949e"},
        textposition="outside",
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20,b=24,l=36,r=6),height=210,
        font={"color":"#484f58","family":"JetBrains Mono","size":9},showlegend=False,
        xaxis={"gridcolor":"#161b22","tickfont":{"size":9},"zeroline":False,"showline":False},
        yaxis={"ticksuffix":"%","gridcolor":"#161b22","tickfont":{"size":8},"zeroline":False})
    return fig


def build_radar(individual_metrics):
    """Multi-metric radar per ticker"""
    tickers=list(individual_metrics.keys())[:6]
    fig=go.Figure()
    categories=["Return","Sharpe","Low Vol","Weight","Low DD"]
    all_ret=[individual_metrics[t]["annualized_return"] for t in tickers]
    all_sh=[individual_metrics[t]["sharpe"] for t in tickers]
    all_vol=[individual_metrics[t]["volatility"] for t in tickers]
    all_w=[individual_metrics[t]["weight"] for t in tickers]

    def norm(vals,invert=False):
        mn,mx=min(vals),max(vals)
        if mx==mn: return [50]*len(vals)
        n=[(v-mn)/(mx-mn)*100 for v in vals]
        return [100-v for v in n] if invert else n

    norm_ret=norm(all_ret)
    norm_sh=norm(all_sh)
    norm_vol=norm(all_vol,invert=True)
    norm_w=norm(all_w)

    rgb_list=["0,212,255","124,77,255","0,229,160","245,197,66","255,112,67","255,64,129"]
    for i,t in enumerate(tickers):
        vals=[norm_ret[i],norm_sh[i],norm_vol[i],norm_w[i],norm_sh[i]]
        rgb=rgb_list[i%len(rgb_list)]
        fig.add_trace(go.Scatterpolar(
            r=vals+[vals[0]],theta=categories+[categories[0]],
            fill="toself",fillcolor=f"rgba({rgb},0.08)",
            line={"color":CHART_COLORS[i%len(CHART_COLORS)],"width":1.5},
            name=t,
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        polar={"bgcolor":"rgba(0,0,0,0)","radialaxis":{"visible":True,"range":[0,100],"tickfont":{"size":7,"color":"#484f58"},"gridcolor":"#21262d","linecolor":"#21262d"},"angularaxis":{"tickfont":{"size":9,"color":"#8b949e"},"gridcolor":"#21262d","linecolor":"#21262d"}},
        showlegend=True,legend={"font":{"size":9,"color":"#8b949e","family":"JetBrains Mono"},"bgcolor":"rgba(0,0,0,0)"},
        margin=dict(t=20,b=20,l=20,r=20),height=230,
    )
    return fig


def build_rolling_vol(cum_returns_dict):
    """Rolling 30d volatility"""
    try:
        s=pd.Series(cum_returns_dict)
        returns=s.pct_change().dropna()
        rolling_vol=returns.rolling(30).std()*np.sqrt(252)*100
        rolling_vol=rolling_vol.dropna()
        fig=go.Figure()
        fig.add_trace(go.Scatter(
            x=list(rolling_vol.index),y=list(rolling_vol.values),
            line={"color":"#7c4dff","width":1.5},
            fill="tozeroy",fillcolor="rgba(124,77,255,0.05)",
            hovertemplate="<b>%{x}</b><br>Vol: %{y:.2f}%<extra></extra>"))
        l=bc(190)
        l["yaxis"]["ticksuffix"]="%"
        fig.update_layout(**l)
        return fig
    except:
        return None


@app.callback(
    Output("results","children"), Output("err-msg","children"), Output("portfolio-store","data"),
    Input("analyze-btn","n_clicks"),
    [State({"type":"ticker","index":i},"value") for i in range(8)]+
    [State({"type":"weight","index":i},"value") for i in range(8)]+
    [State("period-store","value")],
    prevent_initial_call=True,
)
def analyze(_,*args):
    tickers_raw=list(args[:8]); weights_raw=list(args[8:16]); period=args[16] or "1y"
    pairs=[(str(t).strip().upper(),float(w)) for t,w in zip(tickers_raw,weights_raw) if t and str(t).strip() and w is not None and float(w)>0]
    if len(pairs)<2: return no_update,"Min 2 tickers required",no_update
    tickers=[p[0] for p in pairs]; total=sum(p[1] for p in pairs); weights=[p[1]/total for p in pairs]
    try:
        resp=requests.post(f"{API_URL}/analyze",json={"tickers":tickers,"weights":weights,"period":period},timeout=120)
        if resp.status_code!=200: return no_update,resp.json().get("detail","Error"),no_update
        data=resp.json()
    except requests.exceptions.ConnectionError:
        return no_update,"API offline — start Terminal 1",no_update
    except Exception as e:
        return no_update,str(e),no_update

    m=data["metrics"]; ai=data["ai_insights"]; rc=RISK_COLORS.get(ai["risk_label"],"#f5c542")

    def vc(v,pg=True):
        if pg: return "#00e5a0" if v>0 else "#f85149"
        return "#f85149" if v>0 else "#00e5a0"

    def mcard(lbl,val,sfx,c,badge,idx,sub=""):
        return html.Div([
            html.Div([html.Span(lbl,className="m-lbl"),html.Span(badge,className="m-badge")],className="m-top"),
            html.Div(f"{fmt(val)}{sfx}",className="m-val",style={"color":c}),
            html.Div(sub,className="m-sub") if sub else None,
        ],className=f"m-card fi d{idx}")

    sc="#00e5a0" if m["sharpe_ratio"]>1 else "#f5c542" if m["sharpe_ratio"]>0.5 else "#f85149"
    dc="#f85149" if m["max_drawdown"]<-20 else "#f5c542" if m["max_drawdown"]<-10 else "#00e5a0"

    metrics=html.Div([
        mcard("Ann. Return",m["annualized_return"],"%",vc(m["annualized_return"]),"1Y",1,"annualized"),
        mcard("Volatility",m["volatility"],"%","#f5c542","ANN",1,"annualized σ"),
        mcard("Sharpe Ratio",m["sharpe_ratio"],"",sc,"RF5%",2,"risk-adjusted"),
        mcard("Sortino",m["sortino_ratio"],"",sc,"DOWN",2,"downside risk"),
        mcard("Max Drawdown",m["max_drawdown"],"%",dc,"P-T",3,"peak to trough"),
        mcard("Beta",m["beta"],"","#e6edf3","SPY",3,"vs market"),
        mcard("95% VaR",m["var_95"]["var_historical"],"%","#f85149","HIST",4,"daily tail"),
        mcard("CVaR",m["var_95"]["cvar"],"%","#f85149","95%",4,"exp. shortfall"),
    ],className="m-grid")

    # Risk panel
    # Derived unique stats not shown in metric cards
    rr_ratio = round(abs(m["annualized_return"] / m["max_drawdown"]), 2) if m["max_drawdown"] != 0 else 0
    tail_ratio = round(abs(m["var_95"]["var_historical"] / m["var_95"]["cvar"]), 2) if m["var_95"]["cvar"] != 0 else 0
    diversification = max(0, min(100, round(100 - max(data["sector_exposure"].values()), 0))) if data["sector_exposure"] else 0
    n_assets = len(tickers)

    def derived_stat(label, value, sublabel, color="#e6edf3"):
        return html.Div([
            html.Div(label, style={"fontFamily":"JetBrains Mono,monospace","fontSize":"8px","color":"#484f58","letterSpacing":"2px","textTransform":"uppercase","marginBottom":"5px"}),
            html.Div(str(value), style={"fontFamily":"JetBrains Mono,monospace","fontSize":"22px","fontWeight":"700","color":color,"lineHeight":"1"}),
            html.Div(sublabel, style={"fontSize":"10px","color":"#484f58","marginTop":"4px"}),
        ], style={"padding":"14px 16px","background":"#0d1117","borderRadius":"8px","border":"1px solid #21262d"})

    rr_color = "#00e5a0" if rr_ratio > 3 else "#f5c542" if rr_ratio > 1.5 else "#f85149"
    div_color = "#00e5a0" if diversification > 60 else "#f5c542" if diversification > 30 else "#f85149"

    insight=html.Div([sh("Risk Intelligence"),
        # Row 1: gauge + derived stats
        html.Div([
            html.Div([
                dcc.Graph(figure=mk_gauge(ai["risk_score"],ai["risk_label"]),config={"displayModeBar":False},style={"height":"160px","width":"190px"}),
                html.Div(ai["risk_label"],className="risk-label",style={"color":rc,"textAlign":"center","marginTop":"-4px"}),
            ]),
            html.Div([
                derived_stat("Risk / Reward", rr_ratio, "return ÷ drawdown", rr_color),
                derived_stat("Tail Ratio", tail_ratio, "VaR ÷ CVaR", "#7c4dff"),
                derived_stat("Diversification", f"{diversification}%", "non-top sector", div_color),
                derived_stat("Holdings", n_assets, "active positions", "#58a6ff"),
            ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"8px","flex":"1"}),
        ], style={"display":"flex","gap":"20px","alignItems":"center","marginBottom":"20px","paddingBottom":"20px","borderBottom":"1px solid #21262d"}),
        # Row 2: AI text in 3 columns
        html.Div([
            html.Div([html.Div("Summary",className="ai-sub",style={"marginTop":"0"}),html.Div(ai["risk_summary"],className="ai-txt")]),
            html.Div([html.Div("Sector Concentration",className="ai-sub",style={"marginTop":"0"}),html.Div(ai["sector_insights"],className="ai-txt")]),
            html.Div([html.Div("Correlation Risk",className="ai-sub",style={"marginTop":"0"}),html.Div(ai["correlation_insights"],className="ai-txt")]),
        ], style={"display":"grid","gridTemplateColumns":"1fr 1fr 1fr","gap":"20px"}),
    ],className="qp fi d2")

    # Recs
    recs=html.Div([sh("Recommendations"),
        html.Div([html.Div([html.Div(str(i+1),className="rec-n"),html.Div(r,className="rec-t")],className="rec-card") for i,r in enumerate(ai["recommendations"])],className="rec-grid"),
    ],className="qp fi d3")

    # Chart row 1: cumulative + sector
    cum=pd.Series(data["cumulative_returns"])
    cum_fig=go.Figure()
    cum_fig.add_trace(go.Scatter(x=list(cum.index),y=list(cum.values),fill="tozeroy",fillcolor="rgba(0,212,255,0.05)",line={"color":"#00d4ff","width":2},hovertemplate="<b>%{x}</b><br>%{y:.4f}<extra></extra>"))
    cum_fig.update_layout(**bc(230))

    sec_d=data["sector_exposure"]
    sec_fig=go.Figure(go.Pie(labels=list(sec_d.keys()),values=list(sec_d.values()),hole=0.55,
        marker={"colors":CHART_COLORS,"line":{"color":"#0d1117","width":2}},
        textfont={"size":9,"family":"JetBrains Mono"}))
    sec_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",margin=dict(t=4,b=4,l=4,r=4),height=230,
        showlegend=True,legend={"font":{"color":"#484f58","size":9,"family":"JetBrains Mono"},"bgcolor":"rgba(0,0,0,0)"})

    row1=html.Div([
        html.Div([sh("Cumulative Returns"),dcc.Graph(figure=cum_fig,config={"displayModeBar":False})],className="qp fi d4",style={"gridColumn":"span 2"}),
        html.Div([sh("Sector Exposure"),dcc.Graph(figure=sec_fig,config={"displayModeBar":False})],className="qp fi d4"),
    ],style={"display":"grid","gridTemplateColumns":"2fr 1fr","gap":"10px","marginBottom":"12px"})

    # Chart row 2: correlation + VaR + radar
    corr=data["correlation_matrix"]; ct=list(corr.keys())
    cm_v=[[corr[t1].get(t2,0) for t2 in ct] for t1 in ct]
    corr_fig=go.Figure(go.Heatmap(z=cm_v,x=ct,y=ct,
        colorscale=[[0,"#f85149"],[0.5,"#161b22"],[1,"#00d4ff"]],zmid=0,zmin=-1,zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in cm_v],texttemplate="%{text}",
        textfont={"size":9,"color":"#e6edf3","family":"JetBrains Mono"},showscale=False))
    corr_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",margin=dict(t=4,b=4,l=4,r=4),height=230,
        xaxis={"tickfont":{"size":9,"color":"#484f58"}},yaxis={"tickfont":{"size":9,"color":"#484f58"}})

    radar_fig=build_radar(data["individual_metrics"])
    var_fig=build_var_chart(m["var_95"]["var_historical"],m["var_95"]["var_parametric"],m["var_95"]["cvar"])

    row2=html.Div([
        html.Div([sh("Correlation Matrix"),dcc.Graph(figure=corr_fig,config={"displayModeBar":False})],className="qp fi d5"),
        html.Div([sh("VaR Breakdown"),dcc.Graph(figure=var_fig,config={"displayModeBar":False})],className="qp fi d5"),
        html.Div([sh("Holdings Radar"),dcc.Graph(figure=radar_fig,config={"displayModeBar":False})],className="qp fi d5"),
    ],style={"display":"grid","gridTemplateColumns":"1fr 1fr 1fr","gap":"10px","marginBottom":"12px"})

    # Chart row 3: waterfall + monthly heatmap + rolling vol
    wf_fig=build_waterfall(data["individual_metrics"])
    mh_fig=build_returns_dist(data["cumulative_returns"])
    rv_fig=build_rolling_vol(data["cumulative_returns"])

    row3_panels=[]
    if wf_fig: row3_panels.append(html.Div([sh("Return Contribution"),dcc.Graph(figure=wf_fig,config={"displayModeBar":False})],className="qp fi d6"))
    if mh_fig: row3_panels.append(html.Div([sh("Monthly Returns Heatmap"),dcc.Graph(figure=mh_fig,config={"displayModeBar":False})],className="qp fi d6"))
    if rv_fig: row3_panels.append(html.Div([sh("Rolling 30d Volatility"),dcc.Graph(figure=rv_fig,config={"displayModeBar":False})],className="qp fi d6"))

    if len(row3_panels)==3:
        # waterfall + heatmap top row, rolling vol full width below
        row3=html.Div([
            html.Div([row3_panels[0],row3_panels[1]],style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"10px","marginBottom":"10px"}),
            row3_panels[2],
        ],style={"marginBottom":"12px"})
    elif len(row3_panels)==2:
        row3=html.Div(row3_panels,style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"10px","marginBottom":"12px"})
    else:
        row3=html.Div(row3_panels,style={"marginBottom":"12px"})

    # World map
    world=html.Div([sh("Geographic Revenue Exposure"),dcc.Graph(figure=build_geo(tickers,weights),config={"displayModeBar":False})],className="qp fi d7")

    # Holdings table
    holdings=html.Div([sh("Holdings Breakdown"),
        html.Table([
            html.Thead(html.Tr([html.Th(h) for h in ["Ticker","Weight","Ann. Return","Volatility","Sharpe","Contribution"]])),
            html.Tbody([html.Tr([
                html.Td(t,className="tc"),
                html.Td(f"{fmt(v['weight'])}%"),
                html.Td(f"{fmt(v['annualized_return'])}%",style={"color":vc(v['annualized_return'])}),
                html.Td(f"{fmt(v['volatility'])}%",style={"color":"#f5c542"}),
                html.Td(f"{fmt(v['sharpe'])}",style={"color":vc(v['sharpe'])}),
                html.Td(f"{fmt(v['weight']*v['annualized_return']/100,3)}%",style={"color":"#8b949e"}),
            ]) for t,v in data["individual_metrics"].items()]),
        ],className="q-tbl"),
    ],className="qp fi d8")

    # News
    news_items=[]
    for i,a in list(enumerate(data.get("news",[])+data.get("macro_news",[])))[:8]:
        tag="PORTFOLIO" if i<len(data.get("news",[])) else "MACRO"
        tc,bg=("#00d4ff","rgba(0,212,255,0.08)") if tag=="PORTFOLIO" else ("#7c4dff","rgba(124,77,255,0.08)")
        news_items.append(html.Div([
            html.Span(tag,className="news-tag",style={"color":tc,"background":bg,"border":f"1px solid {tc}40"}),
            html.A(a["title"],href=a.get("url","#"),target="_blank",className="news-title"),
            html.Div(a.get("content","")[:160]+"...",className="news-snippet"),
        ],className="news-item"))

    news=html.Div([sh("Market Intelligence"),
        html.Div(news_items or [html.Div("No news available",style={"color":"#484f58","fontSize":"12px"})]),
    ],className="qp fi d9")

    return html.Div([metrics,insight,recs,row1,row2,row3,world,holdings,news]),"",data


@app.callback(Output("chat-input","value"),
    [Input("hint-1","n_clicks"),Input("hint-2","n_clicks"),Input("hint-3","n_clicks"),Input("hint-4","n_clicks")],
    prevent_initial_call=True)
def fill_hint(*_):
    ctx=dash.callback_context
    if not ctx.triggered: return no_update
    hints={"hint-1":"Why is my Sharpe ratio low?","hint-2":"How can I reduce my portfolio beta?","hint-3":"Am I overexposed to any sector?","hint-4":"Give me rebalancing tips for this portfolio"}
    return hints.get(ctx.triggered[0]["prop_id"].split(".")[0],no_update)


# STEP 1: Immediately show user bubble + thinking dots
@app.callback(
    Output("chat-messages","children"),
    Output("chat-store","data"),
    Input("chat-send","n_clicks"),
    State("chat-input","value"),
    State("chat-messages","children"),
    State("chat-store","data"),
    prevent_initial_call=True,
)
def chat_step1(_,question,history,store):
    if not question or not question.strip(): return no_update,no_update
    history=history or []
    user_bubble=html.Div(html.Div(question,className="b-user"),className="bw-user")
    thinking=html.Div([
        html.Div("AI",className="bot-av"),
        html.Div([
            html.Div("NOVA",className="b-lbl"),
            html.Div([html.Span(),html.Span(),html.Span()],className="typing"),
        ],className="b-bot"),
    ],className="bw-bot",id="thinking-bubble")
    new_store=(store or [])+[question]
    return history+[user_bubble,thinking],new_store


# STEP 2: Replace thinking dots with actual answer
@app.callback(
    Output("chat-messages","children",allow_duplicate=True),
    Output("chat-input","value", allow_duplicate=True),
    Input("chat-store","data"),
    State("chat-messages","children"),
    State("portfolio-store","data"),
    prevent_initial_call=True,
)
def chat_step2(store,history,portfolio_data):
    if not store: return no_update,no_update
    question=store[-1]
    history=history or []

    if not portfolio_data:
        answer="Run a portfolio analysis first before asking questions."
    else:
        try:
            m=portfolio_data.get("metrics",{}); ai=portfolio_data.get("ai_insights",{})
            prompt=f"""You are a portfolio risk analyst. Answer concisely using specific numbers.
Portfolio: {portfolio_data.get('tickers',[])}
Return: {m.get('annualized_return')}% | Vol: {m.get('volatility')}% | Sharpe: {m.get('sharpe_ratio')} | Beta: {m.get('beta')}
Max DD: {m.get('max_drawdown')}% | VaR: {m.get('var_95',{}).get('var_historical')}%
Risk: {ai.get('risk_score')}/100 ({ai.get('risk_label')})
Sectors: {portfolio_data.get('sector_exposure',{})}
Question: {question}
Answer in 2-3 sentences with specific numbers."""
            import boto3; from dotenv import load_dotenv; load_dotenv()
            client=boto3.client("bedrock-runtime",region_name=os.getenv("AWS_REGION","us-east-1"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))
            resp=client.invoke_model(modelId="amazon.nova-lite-v1:0",
                body=json.dumps({"messages":[{"role":"user","content":[{"text":prompt}]}],"inferenceConfig":{"max_new_tokens":256,"temperature":0.3}}),
                contentType="application/json",accept="application/json")
            answer=json.loads(resp["body"].read())["output"]["message"]["content"][0]["text"]
        except Exception as e:
            answer=f"Error: {str(e)}"

    # Replace thinking bubble with real answer
    bot_bubble=html.Div([
        html.Div("AI",className="bot-av"),
        html.Div([html.Div("NOVA",className="b-lbl"),answer],className="b-bot"),
    ],className="bw-bot")

    # Remove thinking bubble (last item) and add real answer
    msgs=[m for m in history if not (isinstance(m,dict) and m.get("props",{}).get("id")=="thinking-bubble")]
    return msgs+[bot_bubble],""


if __name__=="__main__":
    port=int(os.getenv("PORT", 8050))
    debug=os.getenv("RAILWAY_ENVIRONMENT") is None
    app.run(debug=debug, host="0.0.0.0", port=port)