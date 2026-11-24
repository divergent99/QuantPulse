import dash
from dash import dcc, html, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
import json
import os
from urllib.parse import quote, urlparse

API_URL = os.getenv("API_URL", "http://localhost:8000")

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    external_scripts=["https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"],
    title="QuantPulse",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)
server = app.server

# ---------------------------------------------------------------- palette
C = {
    "cyan": "#22d3ee", "violet": "#a78bfa", "mint": "#34d399", "amber": "#fbbf24",
    "rose": "#fb7185", "blue": "#60a5fa", "pink": "#f472b6", "orange": "#fb923c",
    "text": "#e8ecf4", "muted": "#94a3b8", "dim": "#64748b",
}
RISK_COLORS = {"Low Risk": C["mint"], "Moderate Risk": C["amber"], "High Risk": C["orange"], "Very High Risk": C["rose"]}
CHART_COLORS = [C["cyan"], C["violet"], C["mint"], C["amber"], C["pink"], C["blue"], C["orange"], C["rose"], "#2dd4bf", "#c084fc"]
FONT_MONO = "JetBrains Mono, ui-monospace, monospace"
FONT_SANS = "Plus Jakarta Sans, system-ui, sans-serif"
GRID = "rgba(148,163,184,0.07)"

PRESETS = {
    "Tech Heavy":        {"tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"], "weights": [25, 25, 20, 15, 15], "color": C["cyan"],   "tag": "Growth tilt"},
    "Balanced":          {"tickers": ["AAPL", "JPM", "JNJ", "XOM", "WMT"],      "weights": [20, 20, 20, 20, 20], "color": C["mint"],   "tag": "Equal weight"},
    "Aggressive Growth": {"tickers": ["NVDA", "TSLA", "AMD", "META", "AMZN"],   "weights": [30, 25, 20, 15, 10], "color": C["rose"],   "tag": "High beta"},
}
GEO_MAP = {
    "AAPL": {"United States": 43, "China": 19, "Europe": 24, "Rest of World": 14},
    "MSFT": {"United States": 50, "Europe": 28, "Asia": 15, "Rest of World": 7},
    "NVDA": {"United States": 40, "China": 17, "Taiwan": 8, "Europe": 20, "Rest of World": 15},
    "GOOGL": {"United States": 47, "Europe": 30, "Asia": 15, "Rest of World": 8},
    "META": {"United States": 45, "Europe": 27, "Asia": 18, "Rest of World": 10},
    "AMZN": {"United States": 62, "Europe": 25, "Rest of World": 13},
    "TSLA": {"United States": 47, "China": 22, "Europe": 23, "Rest of World": 8},
    "JPM": {"United States": 65, "Europe": 20, "Rest of World": 15},
    "JNJ": {"United States": 50, "Europe": 25, "Asia": 15, "Rest of World": 10},
    "XOM": {"United States": 40, "Europe": 15, "Asia": 25, "Rest of World": 20},
    "WMT": {"United States": 70, "China": 5, "Mexico": 6, "Rest of World": 19},
    "AMD": {"United States": 35, "China": 22, "Taiwan": 10, "Europe": 18, "Rest of World": 15},
}
COUNTRY_ISO = {"United States": "USA", "China": "CHN", "Europe": "FRA", "Asia": "JPN", "Taiwan": "TWN", "Mexico": "MEX", "Rest of World": "BRA"}
N_ROWS = 8


def svg_uri(svg):
    return "data:image/svg+xml;utf8," + quote(svg)


LOGO = svg_uri(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#a78bfa"/></linearGradient></defs>'
    '<rect width="32" height="32" rx="9" fill="url(#g)"/>'
    '<path d="M5 17h5l2.5-6 4 11 3-8 2 3H27" fill="none" stroke="#06080d" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)
SPARK = svg_uri(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#06080d">'
    '<path d="M12 2l1.9 5.6L19.5 9.5l-5.6 1.9L12 17l-1.9-5.6L4.5 9.5l5.6-1.9z"/><path d="M19 14l.9 2.6 2.6.9-2.6.9L19 21l-.9-2.6-2.6-.9 2.6-.9z"/></svg>'
)

app.index_string = '''<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#06080d;--panel:rgba(13,17,27,0.72);--panel-2:rgba(19,25,38,0.78);--inset:rgba(6,9,15,0.65);
  --line:rgba(148,163,184,0.09);--line-2:rgba(148,163,184,0.16);
  --text:#e8ecf4;--muted:#94a3b8;--dim:#64748b;--faint:#3b4558;
  --cyan:#22d3ee;--violet:#a78bfa;--mint:#34d399;--amber:#fbbf24;--rose:#fb7185;--blue:#60a5fa;
  --grad:linear-gradient(135deg,#22d3ee 0%,#818cf8 55%,#a78bfa 100%);
  --mono:"JetBrains Mono",monospace;--sans:"Plus Jakarta Sans",system-ui,sans-serif;
  --r:14px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--sans);overflow:hidden;-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(900px 520px at 35% -10%,rgba(34,211,238,0.10),transparent 60%),
    radial-gradient(800px 600px at 105% 108%,rgba(167,139,250,0.15),transparent 60%),
    radial-gradient(600px 400px at 55% 40%,rgba(52,211,153,0.04),transparent 70%)}
body::after{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.5;
  background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);
  background-size:44px 44px;mask-image:radial-gradient(ellipse at 50% 0%,#000 10%,transparent 70%)}
#warp-canvas{opacity:.22!important}
::-webkit-scrollbar{width:6px;height:6px}::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(148,163,184,0.14);border-radius:6px}::-webkit-scrollbar-thumb:hover{background:rgba(148,163,184,0.25)}
#react-entry-point,#_dash-app-content{position:relative;z-index:2}
#qp-wrap{display:grid;grid-template-columns:292px minmax(0,1fr);height:100vh;position:relative;z-index:2}
.glass{background:#090c13;position:relative;z-index:3}
button{font-family:var(--sans)}

/* ------------------------------------------------ SIDEBAR */
#qp-side{transform:translateZ(0);contain:layout paint;border-right:1px solid var(--line);display:flex;flex-direction:column;height:100vh;min-height:0}
.brand{display:flex;align-items:center;gap:12px;padding:20px 20px 18px}
.brand img{width:36px;height:36px;border-radius:10px;display:block;flex-shrink:0}
.brand-name{font-size:17px;font-weight:800;letter-spacing:-0.3px;line-height:1.1}
.brand-name b{color:#7dd3fc;font-weight:800}
.brand-tag{font-size:11px;color:var(--dim);font-weight:500;margin-top:2px}
.side-scroll{flex:1;overflow-y:auto;padding:4px 16px 16px;min-height:0;scrollbar-width:thin;scrollbar-color:transparent transparent}
.side-scroll:hover{scrollbar-color:rgba(148,163,184,0.18) transparent}
.side-scroll::-webkit-scrollbar-thumb{background:transparent}.side-scroll:hover::-webkit-scrollbar-thumb{background:rgba(148,163,184,0.18)}
.s-sec{margin-top:18px}
.s-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.s-lbl{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.8px;text-transform:uppercase}
.s-hint{font-size:11px;color:var(--dim)}

.preset-list{display:flex;flex-direction:column;gap:6px}
.p-card{all:unset;box-sizing:border-box;display:flex;align-items:center;gap:11px;width:100%;cursor:pointer;
  padding:10px 12px;border-radius:11px;background:var(--inset);border:1px solid var(--line);transition:all .18s ease}
.p-card:hover{border-color:color-mix(in srgb,var(--pc) 45%,transparent);background:color-mix(in srgb,var(--pc) 7%,var(--inset));transform:translateX(2px)}
.p-dot{width:30px;height:30px;border-radius:9px;flex-shrink:0;display:flex;align-items:center;justify-content:center;
  background:color-mix(in srgb,var(--pc) 14%,transparent);border:1px solid color-mix(in srgb,var(--pc) 30%,transparent)}
.p-dot i{width:8px;height:8px;border-radius:50%;background:var(--pc);box-shadow:0 0 10px var(--pc)}
.p-name{font-size:13px;font-weight:600;color:var(--text)}
.p-meta{font-family:var(--mono);font-size:10px;color:var(--dim);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.p-tag{margin-left:auto;font-size:10px;font-weight:600;color:var(--pc);white-space:nowrap}

.h-rows{display:flex;flex-direction:column;gap:5px}
.t-grid{display:grid;grid-template-columns:22px 1fr 76px;gap:6px;align-items:center}
.t-idx{font-family:var(--mono);font-size:10px;color:var(--faint);text-align:center}
.qin{background:var(--inset)!important;border:1px solid var(--line)!important;border-radius:9px!important;color:var(--text)!important;
  font-family:var(--mono)!important;font-size:12px!important;font-weight:500!important;padding:7px 10px!important;width:100%!important;transition:all .15s!important;box-shadow:none!important}
.qin.tk{text-transform:uppercase;letter-spacing:.5px}
.qin:hover{border-color:var(--line-2)!important}
.qin:focus{border-color:rgba(34,211,238,0.55)!important;outline:none!important;box-shadow:0 0 0 3px rgba(34,211,238,0.12)!important;background:rgba(6,9,15,0.9)!important}
.qin::placeholder{color:var(--faint)!important;text-transform:none}
.wt-wrap{position:relative}
.wt-wrap::after{content:"%";position:absolute;right:10px;top:50%;transform:translateY(-50%);font-family:var(--mono);font-size:11px;color:var(--dim);pointer-events:none}
.wt-wrap .qin{padding-right:22px!important}
.wt-wrap input::-webkit-outer-spin-button,.wt-wrap input::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
.wt-wrap input[type=number]{-moz-appearance:textfield}

.wt-pill{font-family:var(--mono);font-size:10.5px;font-weight:600;padding:3px 8px;border-radius:999px;border:1px solid var(--line-2);color:var(--dim)}
.wt-pill.ok{color:var(--mint);border-color:rgba(52,211,153,0.35);background:rgba(52,211,153,0.08)}
.wt-pill.warn{color:var(--amber);border-color:rgba(251,191,36,0.35);background:rgba(251,191,36,0.08)}
.alloc{display:flex;height:6px;border-radius:6px;overflow:hidden;background:var(--inset);border:1px solid var(--line);margin-top:10px;gap:2px}
.alloc span{display:block;height:100%;transition:width .3s ease}
.alloc-note{font-size:11px;color:var(--dim);margin-top:7px;line-height:1.45}

.seg{display:grid;grid-template-columns:repeat(4,1fr);gap:3px;padding:3px;background:var(--inset);border:1px solid var(--line);border-radius:11px}
.seg-opt{margin:0!important;text-align:center;font-family:var(--mono);font-size:11.5px;font-weight:600;color:var(--dim);padding:7px 0;border-radius:8px;cursor:pointer;transition:all .15s;user-select:none}
.seg-opt:hover{color:var(--text)}
.seg-in{display:none}
.seg-opt:has(.seg-in:checked){background:var(--panel-2);color:var(--text);box-shadow:0 1px 0 rgba(255,255,255,0.05) inset,0 4px 14px rgba(0,0,0,0.35);outline:1px solid var(--line-2)}

.side-foot{padding:14px 16px 16px;border-top:1px solid var(--line)}
.run-row{display:flex;gap:8px}
.clear-btn{all:unset;box-sizing:border-box;cursor:pointer;width:48px;flex-shrink:0;border-radius:12px;display:flex;align-items:center;justify-content:center;
  font-size:19px;font-weight:700;color:var(--muted);background:var(--inset);border:1px solid var(--line-2);transition:all .18s}
.clear-btn:hover{color:var(--rose);border-color:rgba(251,113,133,0.45);background:rgba(251,113,133,0.08)}
.clear-btn span{display:inline-block;transition:transform .35s ease}.clear-btn:hover span{transform:rotate(-180deg)}
.run-btn{all:unset;box-sizing:border-box;width:100%;display:flex;align-items:center;justify-content:center;gap:9px;cursor:pointer;
  background:var(--grad);color:#06080d;font-weight:700;font-size:14px;padding:12px;border-radius:12px;
  box-shadow:0 8px 28px rgba(56,189,248,0.25),inset 0 1px 0 rgba(255,255,255,0.35);transition:all .2s ease}
.run-btn:hover{transform:translateY(-1px);box-shadow:0 12px 36px rgba(129,140,248,0.38),inset 0 1px 0 rgba(255,255,255,0.35);filter:saturate(1.15)}
.run-btn:active{transform:translateY(0)}
.run-btn .k{font-family:var(--mono);font-size:10px;font-weight:600;padding:2px 6px;border-radius:5px;background:rgba(6,8,13,0.16)}
.err{font-size:12px;color:var(--rose);margin-top:9px;line-height:1.45;text-align:center}
.err:empty{display:none}
.foot-meta{display:flex;justify-content:center;gap:12px;margin-top:11px;font-size:10.5px;color:var(--dim)}
.foot-meta span::before{content:"";display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--mint);margin-right:6px;vertical-align:middle}
.foot-meta span:last-child::before{background:var(--violet)}

/* ------------------------------------------------ MAIN */
#qp-main{overflow-y:auto;height:100vh;min-width:0}
.main-inner{padding:20px 26px 100px;max-width:1500px;margin:0 auto}
.topbar{display:flex;align-items:center;gap:14px;margin-bottom:20px;padding:2px 0 0}
.crumb{font-size:12px;color:var(--dim);font-weight:500}
.crumb b{color:var(--muted);font-weight:600}
.page-title{font-size:22px;font-weight:800;letter-spacing:-0.5px;line-height:1.2;margin-top:2px}
.page-sub{font-size:12.5px;color:var(--dim);margin-top:3px}
.top-right{margin-left:auto;display:flex;gap:8px;align-items:center}
.chip{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:500;color:var(--muted);padding:7px 12px;border-radius:999px;border:1px solid var(--line);background:var(--panel)}
.chip.mono{font-family:var(--mono);font-size:11.5px;color:var(--text)}
.live-dot{width:7px;height:7px;border-radius:50%;background:var(--mint);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(52,211,153,0.5)}60%{box-shadow:0 0 0 6px rgba(52,211,153,0)}}

/* cards */
.qp{position:relative;background:var(--panel);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid var(--line);border-radius:var(--r);padding:18px 18px 16px;margin-bottom:14px;
  box-shadow:0 1px 0 rgba(255,255,255,0.03) inset,0 20px 40px -24px rgba(0,0,0,0.6);transition:border-color .2s}
.qp:hover{border-color:var(--line-2)}
.grid{display:grid;gap:14px;margin-bottom:14px}.grid>.qp{margin-bottom:0}
.g-2{grid-template-columns:1fr 1fr}.g-3{grid-template-columns:repeat(3,1fr)}.g-21{grid-template-columns:2fr 1fr}
.sh{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.sh-ic{width:8px;height:8px;border-radius:3px;background:var(--sc,var(--cyan));box-shadow:0 0 12px var(--sc,var(--cyan))}
.sh-txt{font-size:14px;font-weight:700;color:var(--text);letter-spacing:-0.1px}
.sh-cap{margin-left:auto;font-size:11.5px;color:var(--dim)}

/* metric cards */
.m-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:14px}
.m-card{position:relative;overflow:hidden;background:var(--panel);backdrop-filter:blur(14px);border:1px solid var(--line);border-radius:var(--r);padding:16px 16px 15px;transition:all .22s ease}
.m-card::before{content:"";position:absolute;inset:0;background:radial-gradient(260px 120px at 100% 0%,color-mix(in srgb,var(--accent) 16%,transparent),transparent 70%);pointer-events:none}
.m-card::after{content:"";position:absolute;left:16px;right:16px;bottom:0;height:2px;border-radius:2px;background:linear-gradient(90deg,var(--accent),transparent);opacity:.7}
.m-card:hover{transform:translateY(-3px);border-color:color-mix(in srgb,var(--accent) 35%,transparent);box-shadow:0 16px 36px -14px color-mix(in srgb,var(--accent) 35%,transparent)}
.m-top{display:flex;align-items:center;gap:10px;margin-bottom:14px;position:relative}
.m-ic{width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:12px;font-weight:700;
  color:var(--accent);background:color-mix(in srgb,var(--accent) 13%,transparent);border:1px solid color-mix(in srgb,var(--accent) 28%,transparent)}
.m-lbl{font-size:12.5px;font-weight:600;color:var(--muted)}
.m-badge{margin-left:auto;font-family:var(--mono);font-size:9.5px;font-weight:600;color:var(--dim);border:1px solid var(--line-2);border-radius:6px;padding:2px 6px}
.m-val{position:relative;font-family:var(--mono);font-size:27px;font-weight:700;line-height:1;letter-spacing:-1px;color:var(--accent);font-variant-numeric:tabular-nums}
.m-sub{position:relative;font-size:11.5px;color:var(--dim);margin-top:8px}

/* risk */
.risk-row{display:grid;grid-template-columns:230px 1fr;gap:20px;align-items:center;padding-bottom:18px;margin-bottom:18px;border-bottom:1px solid var(--line)}
.gauge-box{display:flex;flex-direction:column;align-items:center;padding:6px 0;border-radius:12px;background:radial-gradient(160px 120px at 50% 60%,color-mix(in srgb,var(--rc) 12%,transparent),transparent 70%)}
.risk-label{font-family:var(--mono);font-weight:700;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:var(--rc);padding:5px 12px;border-radius:999px;border:1px solid color-mix(in srgb,var(--rc) 35%,transparent);background:color-mix(in srgb,var(--rc) 10%,transparent);margin-top:-2px}
.d-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.d-stat{padding:14px 15px;background:var(--inset);border:1px solid var(--line);border-radius:12px;position:relative;overflow:hidden}
.d-stat::before{content:"";position:absolute;left:0;top:12px;bottom:12px;width:3px;border-radius:0 3px 3px 0;background:var(--accent)}
.d-lbl{font-size:11.5px;font-weight:600;color:var(--muted);margin-bottom:6px}
.d-val{font-family:var(--mono);font-size:22px;font-weight:700;line-height:1;color:var(--accent)}
.d-sub{font-size:11px;color:var(--dim);margin-top:5px}
.ai-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.ai-card{padding:14px 15px;border-radius:12px;background:var(--inset);border:1px solid var(--line)}
.ai-sub{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--text);margin-bottom:8px}
.ai-sub i{width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 8px var(--accent)}
.ai-txt{font-size:13px;color:var(--muted);line-height:1.7}

/* recs */
.rec-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.rec-card{background:var(--inset);border:1px solid var(--line);border-radius:12px;padding:13px 14px;display:flex;gap:12px;align-items:flex-start;transition:all .18s}
.rec-card:hover{border-color:rgba(34,211,238,0.3);transform:translateY(-1px)}
.rec-n{font-family:var(--mono);font-size:12px;font-weight:700;color:#06080d;background:var(--grad);border-radius:8px;width:26px;height:26px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.rec-t{font-size:13px;color:var(--text);opacity:.86;line-height:1.55}

/* table */
.q-tbl{width:100%;border-collapse:separate;border-spacing:0}
.q-tbl th{font-size:11px;font-weight:600;color:var(--dim);text-transform:uppercase;letter-spacing:.6px;padding:9px 14px;border-bottom:1px solid var(--line);text-align:left;background:var(--inset)}
.q-tbl th:first-child{border-radius:10px 0 0 0}.q-tbl th:last-child{border-radius:0 10px 0 0}
.q-tbl td{font-family:var(--mono);font-size:12.5px;padding:11px 14px;border-bottom:1px solid var(--line);color:var(--muted)}
.q-tbl tr:last-child td{border-bottom:none}
.q-tbl tbody tr{transition:background .12s}.q-tbl tbody tr:hover td{background:rgba(34,211,238,0.035)}
.tc{display:flex;align-items:center;gap:9px;color:var(--text)!important;font-weight:700}
.tc i{width:8px;height:8px;border-radius:2px}
.wbar{display:flex;align-items:center;gap:9px}.wbar div{flex:1;max-width:90px;height:4px;border-radius:4px;background:var(--line)}
.wbar div span{display:block;height:100%;border-radius:4px;background:var(--grad)}

/* news */
.news-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.qp,.grid>*{min-width:0}
.news-item{display:block;min-width:0;overflow:hidden;overflow-wrap:anywhere;word-break:break-word;text-decoration:none;padding:14px 15px;border-radius:12px;background:var(--inset);border:1px solid var(--line);transition:all .18s}
.news-item:hover{border-color:var(--line-2);transform:translateY(-2px);background:rgba(13,17,27,0.9)}
.news-top{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.news-tag{font-family:var(--mono);font-size:9.5px;font-weight:700;letter-spacing:.8px;padding:3px 7px;border-radius:6px}
.news-src{font-size:11px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.news-title{font-size:13.5px;color:var(--text);line-height:1.45;font-weight:600;margin-bottom:6px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.news-item:hover .news-title{color:var(--cyan)}
.news-snippet{font-size:12px;color:var(--dim);line-height:1.55;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

/* loading */
.loading-wrap{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:68vh;gap:26px}
.orbit{position:relative;width:84px;height:84px}
.orbit::before,.orbit::after{content:"";position:absolute;inset:0;border-radius:50%;border:2px solid transparent}
.orbit::before{border-top-color:var(--cyan);border-right-color:var(--cyan);animation:spin 1s linear infinite}
.orbit::after{inset:12px;border-bottom-color:var(--violet);border-left-color:var(--violet);animation:spin 1.4s linear infinite reverse}
.orbit img{position:absolute;inset:28px;width:28px;height:28px;border-radius:8px}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-txt{font-size:18px;font-weight:700;letter-spacing:-0.2px}
.loading-steps{display:flex;flex-direction:column;gap:8px;min-width:280px}
.loading-step{display:flex;align-items:center;gap:11px;font-size:13px;color:var(--faint);padding:10px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel);animation:stepOn .4s ease forwards}
.loading-step i{width:8px;height:8px;border-radius:50%;background:var(--faint)}
.loading-step:nth-child(1){animation-delay:.1s}.loading-step:nth-child(2){animation-delay:2.5s}.loading-step:nth-child(3){animation-delay:5s}.loading-step:nth-child(4){animation-delay:9s}
@keyframes stepOn{to{color:var(--text);border-color:rgba(34,211,238,0.28)}}
.loading-step:nth-child(n) i{animation:dotOn .4s ease forwards;animation-delay:inherit}
@keyframes dotOn{to{background:var(--cyan);box-shadow:0 0 10px var(--cyan)}}

/* empty */
.empty{display:flex;flex-direction:column;align-items:center;text-align:center;padding:56px 24px 40px}
.e-icon{width:64px;height:64px;border-radius:18px;display:flex;align-items:center;justify-content:center;background:var(--grad);box-shadow:0 18px 50px rgba(56,189,248,0.3);margin-bottom:22px}
.e-icon img{width:64px;height:64px;border-radius:18px}
.e-txt{font-size:30px;font-weight:800;letter-spacing:-1px;line-height:1.15;max-width:560px}
.e-txt span{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.e-sub{font-size:14.5px;color:var(--muted);margin-top:12px;max-width:500px;line-height:1.6}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:34px;width:100%;max-width:760px}
.step{text-align:left;padding:18px;border-radius:var(--r);background:var(--panel);border:1px solid var(--line);backdrop-filter:blur(14px)}
.step-n{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--cyan);margin-bottom:10px}
.step-t{font-size:14px;font-weight:700;margin-bottom:5px}
.step-d{font-size:12.5px;color:var(--dim);line-height:1.5}
.caps{display:flex;flex-wrap:wrap;justify-content:center;gap:7px;margin-top:22px;max-width:700px}
.cap{font-family:var(--mono);font-size:11px;color:var(--muted);padding:5px 10px;border-radius:999px;border:1px solid var(--line);background:var(--inset)}

/* ------------------------------------------------ CHAT */
#qp-chat{position:fixed;right:24px;bottom:96px;width:410px;height:min(660px,calc(100vh - 124px));z-index:60;display:flex;flex-direction:column;min-height:0;overflow:hidden;
  background:#0a0d15;border:1px solid var(--line-2);border-radius:20px;box-shadow:0 40px 90px -20px rgba(0,0,0,0.85),0 0 0 1px rgba(129,140,248,0.08);
  transform-origin:bottom right;transform:translateY(14px) scale(.94);opacity:0;visibility:hidden;pointer-events:none;
  transition:opacity .22s ease,transform .26s cubic-bezier(.2,.8,.2,1),visibility 0s linear .26s}
#qp-chat.open{opacity:1;transform:none;visibility:visible;pointer-events:auto;transition:opacity .22s ease,transform .26s cubic-bezier(.2,.8,.2,1),visibility 0s}
.chat-close{all:unset;cursor:pointer;margin-left:auto;width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;color:var(--dim);font-size:18px;border:1px solid var(--line);transition:all .15s}
.chat-close:hover{color:var(--text);border-color:var(--line-2);background:var(--inset)}
.chat-fab{all:unset;box-sizing:border-box;position:fixed;right:24px;bottom:24px;z-index:61;cursor:pointer;height:54px;padding:0 20px 0 8px;border-radius:999px;
  display:flex;align-items:center;gap:10px;background:var(--grad);color:#06080d;font-weight:700;font-size:14px;
  box-shadow:0 14px 40px rgba(129,140,248,0.45),inset 0 1px 0 rgba(255,255,255,0.35);transition:all .22s cubic-bezier(.2,.8,.2,1)}
.chat-fab:hover{transform:translateY(-2px);box-shadow:0 18px 48px rgba(129,140,248,0.55),inset 0 1px 0 rgba(255,255,255,0.35)}
.fab-ic{width:38px;height:38px;border-radius:50%;background:rgba(6,8,13,0.16);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800}
.fab-ic img{width:20px;height:20px}
.fab-x{display:none}
.chat-fab.open{padding:0 8px;width:54px;justify-content:center}
.chat-fab.open .fab-txt,.chat-fab.open .fab-ic img{display:none}
.chat-fab.open .fab-x{display:block}
.chat-fab.ready:not(.open)::after{content:"";position:absolute;top:2px;right:2px;width:12px;height:12px;border-radius:50%;background:var(--mint);border:2px solid #06080d;animation:pulse 2s infinite}
.chat-top{padding:18px 18px 14px;border-bottom:1px solid var(--line)}
.chat-id{display:flex;align-items:center;gap:12px}
.chat-av{position:relative;width:38px;height:38px;border-radius:12px;background:var(--grad);display:flex;align-items:center;justify-content:center;box-shadow:0 6px 22px rgba(129,140,248,0.35)}
.chat-av img{width:20px;height:20px}
.chat-av::after{content:"";position:absolute;right:-2px;bottom:-2px;width:11px;height:11px;border-radius:50%;background:var(--mint);border:2px solid #0b0f18}
.chat-title{font-size:15px;font-weight:700}
.chat-sub{font-size:11.5px;color:var(--dim);margin-top:1px}
.ctx{display:flex;align-items:center;gap:8px;margin-top:13px;padding:9px 11px;border-radius:10px;background:var(--inset);border:1px dashed var(--line-2);font-size:11.5px;color:var(--dim)}
.ctx.on{border-style:solid;border-color:rgba(52,211,153,0.25);color:var(--muted)}
.ctx b{font-family:var(--mono);font-weight:600;color:var(--text)}
.ctx-dot{width:6px;height:6px;border-radius:50%;background:var(--faint);flex-shrink:0}
.ctx.on .ctx-dot{background:var(--mint);box-shadow:0 0 8px var(--mint)}
.chat-msgs{flex:1;overflow-y:auto;padding:18px 16px;display:flex;flex-direction:column;gap:14px;min-height:0}
.bw-user{display:flex;justify-content:flex-end;animation:pop .25s ease}
.bw-bot{display:flex;justify-content:flex-start;align-items:flex-start;gap:10px;animation:pop .25s ease}
@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.bot-av{width:28px;height:28px;border-radius:9px;background:var(--grad);display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
.bot-av img{width:15px;height:15px}
.b-user{background:linear-gradient(135deg,rgba(34,211,238,0.22),rgba(167,139,250,0.22));border:1px solid rgba(129,140,248,0.35);border-radius:16px 16px 4px 16px;padding:10px 14px;font-size:13px;color:var(--text);max-width:86%;line-height:1.5}
.b-bot{background:var(--panel-2);border:1px solid var(--line);border-radius:4px 16px 16px 16px;padding:11px 14px;font-size:13px;color:#cbd5e1;max-width:90%;line-height:1.65}
.b-lbl{font-size:11px;font-weight:700;color:var(--violet);margin-bottom:4px}
.md p{margin:0 0 8px}.md p:last-child{margin-bottom:0}.md ul,.md ol{margin:4px 0 8px 18px}.md li{margin:2px 0}
.md strong{color:var(--text)}.md code{font-family:var(--mono);font-size:11.5px;background:var(--inset);padding:1px 5px;border-radius:5px;color:var(--cyan)}
.typing{display:flex;gap:5px;align-items:center;padding:4px 0}
.typing span{width:6px;height:6px;border-radius:50%;background:var(--violet);opacity:.3;animation:td 1.2s ease-in-out infinite}
.typing span:nth-child(2){animation-delay:.18s}.typing span:nth-child(3){animation-delay:.36s}
@keyframes td{0%,60%,100%{transform:translateY(0);opacity:.3}30%{transform:translateY(-4px);opacity:1}}
.chat-foot{padding:12px 14px 16px;border-top:1px solid var(--line)}
.chat-hints{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.h-chip{font-size:11.5px;font-weight:500;color:var(--muted);border:1px solid var(--line-2);border-radius:999px;padding:5px 11px;cursor:pointer;transition:all .15s;background:var(--inset)}
.h-chip:hover{border-color:rgba(34,211,238,0.45);color:var(--cyan);background:rgba(34,211,238,0.06)}
.chat-inp-row{display:flex;gap:6px;align-items:center;padding:5px 5px 5px 6px;border-radius:14px;background:var(--inset);border:1px solid var(--line-2);transition:all .15s}
.chat-inp-row:focus-within{border-color:rgba(34,211,238,0.5);box-shadow:0 0 0 3px rgba(34,211,238,0.1)}
.chat-inp{flex:1;background:transparent!important;border:none!important;color:var(--text)!important;font-family:var(--sans)!important;font-size:13px!important;padding:7px 8px!important;box-shadow:none!important}
.chat-inp:focus{outline:none!important}
.chat-inp::placeholder{color:var(--dim)!important}
.send-btn{all:unset;box-sizing:border-box;cursor:pointer;width:36px;height:36px;border-radius:10px;background:var(--grad);color:#06080d;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:800;flex-shrink:0;transition:all .15s;box-shadow:0 4px 16px rgba(129,140,248,0.35)}
.send-btn:hover{transform:translateY(-1px);filter:saturate(1.2)}
.chat-note{font-size:10.5px;color:var(--faint);text-align:center;margin-top:9px}

/* entrance */
.fi{opacity:0;transform:translateY(8px);animation:fi .45s cubic-bezier(.2,.7,.2,1) forwards}
.d1{animation-delay:.03s}.d2{animation-delay:.08s}.d3{animation-delay:.13s}.d4{animation-delay:.18s}.d5{animation-delay:.23s}.d6{animation-delay:.28s}.d7{animation-delay:.33s}.d8{animation-delay:.38s}.d9{animation-delay:.43s}
@keyframes fi{to{opacity:1;transform:none}}

/* responsive */
@media (max-width:1440px){#qp-wrap{grid-template-columns:270px minmax(0,1fr)}.m-val{font-size:24px}}
@media (max-width:1200px){.m-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.g-3{grid-template-columns:1fr 1fr}.ai-grid{grid-template-columns:1fr}.risk-row{grid-template-columns:1fr}}
@media (max-width:980px){
  html,body{overflow:auto}
  #qp-wrap{grid-template-columns:1fr;height:auto}
  #qp-side,#qp-main{height:auto;border:none}
  #qp-chat{inset:0;width:auto;height:auto;border-radius:0;bottom:0;right:0}
  .chat-fab{right:16px;bottom:16px}
  .g-2,.g-21,.g-3,.rec-grid,.news-grid,.steps{grid-template-columns:1fr}
}
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>'''


# ---------------------------------------------------------------- helpers
def fmt(v, d=2):
    try:
        return round(float(v), d)
    except (TypeError, ValueError):
        return v


def sh(txt, color=None, cap=None):
    return html.Div([
        html.Span(className="sh-ic"),
        html.Span(txt, className="sh-txt"),
        html.Span(cap, className="sh-cap") if cap else None,
    ], className="sh", style={"--sc": color} if color else None)


def graph(fig):
    return dcc.Graph(figure=fig, config={"displayModeBar": False, "responsive": True})


def theme(fig, h=220, margin=None, pct_y=False, legend=False):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=h,
        margin=margin or dict(t=8, b=28, l=44, r=8),
        font={"color": C["dim"], "family": FONT_MONO, "size": 10},
        showlegend=legend,
        hoverlabel={"bgcolor": "#0e121c", "bordercolor": "rgba(148,163,184,0.25)", "font": {"family": FONT_MONO, "size": 11, "color": C["text"]}},
        xaxis={"gridcolor": GRID, "zeroline": False, "showline": False, "tickfont": {"size": 10}},
        yaxis={"gridcolor": GRID, "zeroline": False, "showline": False, "tickfont": {"size": 10}, "ticksuffix": "%" if pct_y else ""},
    )
    return fig


def ticker_row(i):
    return html.Div([
        html.Span(f"{i + 1:02d}", className="t-idx"),
        dbc.Input(id={"type": "ticker", "index": i}, placeholder="Ticker", className="qin tk", debounce=True),
        html.Div(dbc.Input(id={"type": "weight", "index": i}, placeholder="0", type="number", min=0, max=100, className="qin", debounce=True), className="wt-wrap"),
    ], className="t-grid")


def preset_card(name, p):
    return html.Button([
        html.Div(html.I(), className="p-dot"),
        html.Div([html.Div(name, className="p-name"), html.Div(" · ".join(p["tickers"]), className="p-meta")], style={"minWidth": 0}),
        html.Span(p["tag"], className="p-tag"),
    ], id={"type": "preset", "index": name}, className="p-card", style={"--pc": p["color"]}, n_clicks=0)


# ---------------------------------------------------------------- layout
sidebar = html.Div([
    html.Div([
        html.Img(src=LOGO, alt=""),
        html.Div([html.Div(["Quant", html.B("Pulse")], className="brand-name"), html.Div("Portfolio risk intelligence", className="brand-tag")]),
    ], className="brand"),
    html.Div([
        html.Div([
            html.Div([html.Span("Quick start", className="s-lbl"), html.Span("Load a preset", className="s-hint")], className="s-head"),
            html.Div([preset_card(n, p) for n, p in PRESETS.items()], className="preset-list"),
        ], className="s-sec", style={"marginTop": "4px"}),
        html.Div([
            html.Div([html.Span("Holdings", className="s-lbl"), html.Span("0%", id="wt-total", className="wt-pill")], className="s-head"),
            html.Div([ticker_row(i) for i in range(N_ROWS)], className="h-rows"),
            html.Div(id="alloc-bar", className="alloc"),
            html.Div("Weights are normalised to 100% automatically.", id="alloc-note", className="alloc-note"),
        ], className="s-sec"),
        html.Div([
            html.Div([html.Span("Lookback", className="s-lbl")], className="s-head"),
            dcc.RadioItems(
                id="period-store",
                options=[{"label": l, "value": v} for l, v in [("6M", "6mo"), ("1Y", "1y"), ("2Y", "2y"), ("5Y", "5y")]],
                value="1y", className="seg", labelClassName="seg-opt", inputClassName="seg-in",
            ),
        ], className="s-sec"),
        dcc.Store(id="portfolio-store", data={}),
        dcc.Store(id="chat-store", data=[]),
    ], className="side-scroll"),
    html.Div([
        html.Div([
            html.Button([html.Span("Run Analysis"), html.Span("↵", className="k")], id="analyze-btn", className="run-btn", n_clicks=0),
            html.Button(html.Span("↺"), id="clear-btn", className="clear-btn", n_clicks=0, title="Clear analysis"),
        ], className="run-row"),
        html.Div(id="err-msg", className="err"),
        html.Div([html.Span("Twelve Data"), html.Span("Nova Lite")], className="foot-meta"),
    ], className="side-foot"),
], id="qp-side", className="glass")


def welcome_msgs():
    return [html.Div([
        html.Div(html.Img(src=SPARK, alt=""), className="bot-av"),
        html.Div([
            html.Div("Nova", className="b-lbl"),
            dcc.Markdown("Hey. Run an analysis and I'll have your full risk profile loaded. Then ask me **why** a number looks the way it does, or **what to change**.", className="md"),
        ], className="b-bot"),
    ], className="bw-bot")]


chat_panel = html.Div([
    html.Div([
        html.Div([
            html.Div(html.Img(src=SPARK, alt=""), className="chat-av"),
            html.Div([html.Div("Portfolio Chat", className="chat-title"), html.Div("Amazon Nova Lite · context-aware", className="chat-sub")]),
            html.Button("×", id="chat-close", className="chat-close", n_clicks=0, title="Close"),
        ], className="chat-id"),
        html.Div([html.Span(className="ctx-dot"), html.Span("No portfolio in context yet")], id="chat-context", className="ctx"),
    ], className="chat-top"),
    html.Div(id="chat-messages", children=welcome_msgs(), className="chat-msgs"),
    html.Div([
        html.Div([
            html.Span("Why is my Sharpe low?", id="hint-1", className="h-chip", n_clicks=0),
            html.Span("Reduce beta", id="hint-2", className="h-chip", n_clicks=0),
            html.Span("Overexposed?", id="hint-3", className="h-chip", n_clicks=0),
            html.Span("Rebalancing tips", id="hint-4", className="h-chip", n_clicks=0),
        ], className="chat-hints"),
        html.Div([
            dbc.Input(id="chat-input", placeholder="Ask about your portfolio...", className="chat-inp", autoComplete="off"),
            html.Button("↑", id="chat-send", className="send-btn", n_clicks=0),
        ], className="chat-inp-row"),
        html.Div("AI answers can be wrong. Not financial advice.", className="chat-note"),
    ], className="chat-foot"),
], id="qp-chat")

chat_fab = html.Button([
    html.Span([html.Img(src=SPARK, alt=""), html.Span("×", className="fab-x")], className="fab-ic"),
    html.Span("Ask Nova", className="fab-txt"),
], id="chat-fab", className="chat-fab", n_clicks=0, title="Portfolio chat")


empty_state = html.Div([
    html.Div(html.Img(src=LOGO, alt=""), className="e-icon"),
    html.Div(["Know your ", html.Span("risk"), ", not just your holdings."], className="e-txt"),
    html.Div("Load a portfolio from the sidebar and QuantPulse runs a full quant risk engine, then has Nova explain what it means in plain English.", className="e-sub"),
    html.Div([
        html.Div([html.Div("01", className="step-n"), html.Div("Pick holdings", className="step-t"), html.Div("Start from a preset or type up to 8 tickers.", className="step-d")], className="step"),
        html.Div([html.Div("02", className="step-n"), html.Div("Set weights", className="step-t"), html.Div("Any numbers work. We normalise them to 100%.", className="step-d")], className="step"),
        html.Div([html.Div("03", className="step-n"), html.Div("Run & ask", className="step-t"), html.Div("Get the dashboard, then grill the AI in chat.", className="step-d")], className="step"),
    ], className="steps"),
    html.Div([html.Span(c, className="cap") for c in ["VaR / CVaR", "Sharpe & Sortino", "Beta vs SPY", "Max drawdown", "Correlation", "Sector & geo exposure", "Live news"]], className="caps"),
], className="empty")


app.layout = html.Div([html.Div([
    sidebar,
    html.Div(html.Div([
        html.Div([
            html.Div([
                html.Div([html.B("Workspace"), " / Risk overview"], className="crumb"),
                html.Div("Risk Dashboard", className="page-title"),
                html.Div("Awaiting portfolio", id="topbar-sub", className="page-sub"),
            ]),
            html.Div([
                html.Div([html.Span(className="live-dot"), "Live data"], className="chip"),
                html.Div("--:--:--", id="clock", className="chip mono"),
            ], className="top-right"),
            dcc.Interval(id="clock-iv", interval=1000),
        ], className="topbar"),
        html.Div(id="loading-screen", style={"display": "none"}, children=[
            html.Div([
                html.Div(html.Img(src=LOGO, alt=""), className="orbit"),
                html.Div("Analyzing portfolio", className="loading-txt"),
                html.Div([
                    html.Div([html.I(), "Fetching market data"], className="loading-step"),
                    html.Div([html.I(), "Running quant engine"], className="loading-step"),
                    html.Div([html.I(), "AI risk assessment"], className="loading-step"),
                    html.Div([html.I(), "Pulling market news"], className="loading-step"),
                ], className="loading-steps"),
            ], className="loading-wrap"),
        ]),
        html.Div(id="results", children=[empty_state]),
    ], className="main-inner"), id="qp-main"),
], id="qp-wrap"),
    chat_panel,
    chat_fab,
])


# ---------------------------------------------------------------- client-side
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

app.clientside_callback(
    """
    function(children) {
        var ls = document.getElementById('loading-screen');
        var rs = document.getElementById('results');
        if (ls) ls.style.display = 'none';
        if (rs) rs.style.display = 'block';
        var m = document.getElementById('qp-main'); if (m) m.scrollTo({top: 0, behavior: 'smooth'});
        return window.dash_clientside.no_update;
    }
    """,
    Output("results", "style", allow_duplicate=True),
    Input("results", "children"),
    prevent_initial_call=True,
)

# If analysis fails, drop the loader and bring back whatever was showing before
app.clientside_callback(
    """
    function(msg) {
        if (!msg) return window.dash_clientside.no_update;
        var ls = document.getElementById('loading-screen');
        var rs = document.getElementById('results');
        if (ls) ls.style.display = 'none';
        if (rs) rs.style.display = 'block';
        return window.dash_clientside.no_update;
    }
    """,
    Output("results", "style", allow_duplicate=True),
    Input("err-msg", "children"),
    prevent_initial_call=True,
)

# Floating chat: open/close from the bubble or the header ×, show a dot once a portfolio is loaded
app.clientside_callback(
    """
    function(fab, close, data) {
        var trig = (window.dash_clientside.callback_context.triggered[0] || {}).prop_id || '';
        var panel = document.getElementById('qp-chat');
        var isOpen = panel && panel.classList.contains('open');
        if (trig.indexOf('chat-fab') === 0) isOpen = !isOpen;
        else if (trig.indexOf('chat-close') === 0) isOpen = false;
        var ready = data && Object.keys(data).length ? ' ready' : '';
        if (isOpen) setTimeout(function(){var i=document.getElementById('chat-input'); if(i) i.focus();}, 120);
        return [isOpen ? 'open' : '', 'chat-fab' + ready + (isOpen ? ' open' : '')];
    }
    """,
    Output("qp-chat", "className"), Output("chat-fab", "className"),
    Input("chat-fab", "n_clicks"), Input("chat-close", "n_clicks"), Input("portfolio-store", "data"),
)

# Clock runs in the browser so it doesn't hit the server every second
app.clientside_callback(
    "function(n){var d=new Date();return d.toTimeString().slice(0,8);}",
    Output("clock", "children"),
    Input("clock-iv", "n_intervals"),
)

# Keep the chat scrolled to the newest message
app.clientside_callback(
    """
    function(children) {
        setTimeout(function(){var el=document.getElementById('chat-messages'); if(el) el.scrollTop=el.scrollHeight;}, 60);
        return window.dash_clientside.no_update;
    }
    """,
    Output("chat-messages", "style"),
    Input("chat-messages", "children"),
)


# ---------------------------------------------------------------- sidebar callbacks
@app.callback(
    [Output({"type": "ticker", "index": i}, "value") for i in range(N_ROWS)] +
    [Output({"type": "weight", "index": i}, "value") for i in range(N_ROWS)],
    [Input({"type": "preset", "index": n}, "n_clicks") for n in PRESETS],
    prevent_initial_call=True,
)
def load_preset(*clicks):
    if not ctx.triggered_id or not any(clicks):
        return [no_update] * (N_ROWS * 2)
    p = PRESETS[ctx.triggered_id["index"]]
    pad = N_ROWS - len(p["tickers"])
    return p["tickers"] + [""] * pad + p["weights"] + [None] * pad


@app.callback(
    [Output({"type": "ticker", "index": i}, "value", allow_duplicate=True) for i in range(N_ROWS)] +
    [Output({"type": "weight", "index": i}, "value", allow_duplicate=True) for i in range(N_ROWS)] +
    [Output("results", "children", allow_duplicate=True), Output("portfolio-store", "data", allow_duplicate=True),
     Output("err-msg", "children", allow_duplicate=True), Output("topbar-sub", "children", allow_duplicate=True),
     Output("period-store", "value"), Output("chat-messages", "children", allow_duplicate=True),
     Output("chat-store", "data", allow_duplicate=True)],
    Input("clear-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_all(n):
    if not n:
        return [no_update] * (N_ROWS * 2 + 7)
    return [""] * N_ROWS + [None] * N_ROWS + [[empty_state], {}, "", "Awaiting portfolio", "1y", welcome_msgs(), []]


@app.callback(
    Output("wt-total", "children"), Output("wt-total", "className"),
    Output("alloc-bar", "children"), Output("alloc-note", "children"),
    [Input({"type": "ticker", "index": i}, "value") for i in range(N_ROWS)] +
    [Input({"type": "weight", "index": i}, "value") for i in range(N_ROWS)],
)
def weight_summary(*vals):
    tks, wts = vals[:N_ROWS], vals[N_ROWS:]
    pairs = []
    for t, w in zip(tks, wts):
        try:
            w = float(w)
        except (TypeError, ValueError):
            continue
        if t and str(t).strip() and w > 0:
            pairs.append((str(t).strip().upper(), w))
    total = sum(w for _, w in pairs)
    if not pairs:
        return "0%", "wt-pill", [], "Weights are normalised to 100% automatically."
    segs = [html.Span(title=f"{t} {w / total * 100:.1f}%", style={"width": f"{w / total * 100}%", "background": CHART_COLORS[i % len(CHART_COLORS)]})
            for i, (t, w) in enumerate(pairs)]
    ok = abs(total - 100) < 0.01
    note = f"{len(pairs)} holdings ready." if ok else f"{len(pairs)} holdings · totals {total:g}%, will be scaled to 100%."
    if len(pairs) < 2:
        note = "Add at least 2 holdings to run an analysis."
    return f"{total:g}%", "wt-pill ok" if ok else "wt-pill warn", segs, note


# ---------------------------------------------------------------- charts
def mk_gauge(score, label):
    color = RISK_COLORS.get(label, C["amber"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)", "tickfont": {"color": C["dim"], "size": 9}, "nticks": 5},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(148,163,184,0.06)", "borderwidth": 0,
            "steps": [
                {"range": [0, 25], "color": "rgba(52,211,153,0.10)"}, {"range": [25, 50], "color": "rgba(251,191,36,0.08)"},
                {"range": [50, 75], "color": "rgba(251,146,60,0.08)"}, {"range": [75, 100], "color": "rgba(251,113,133,0.10)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.9, "value": score},
        },
        number={"font": {"color": color, "size": 40, "family": FONT_MONO}, "suffix": ""},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=18, b=0, l=22, r=22), height=165)
    return fig


def build_geo(tickers, weights):
    exp = {}
    for t, w in zip(tickers, weights):
        for c, p in GEO_MAP.get(t, {"United States": 100}).items():
            exp[c] = exp.get(c, 0) + (p * w)
    total = sum(exp.values())
    if total > 0:
        exp = {k: round(v / total * 100, 1) for k, v in exp.items()}
    fig = go.Figure(go.Choropleth(
        locations=[COUNTRY_ISO.get(c, "USA") for c in exp], z=list(exp.values()),
        text=[f"{c}: {v:.1f}%" for c, v in exp.items()], hovertemplate="%{text}<extra></extra>",
        colorscale=[[0, "#0f2a3a"], [0.5, "#0e7490"], [1, C["cyan"]]], showscale=False,
        marker_line_color="rgba(34,211,238,0.3)", marker_line_width=0.6))
    theme(fig, 260, margin=dict(t=0, b=0, l=0, r=0))
    fig.update_layout(geo=dict(
        bgcolor="rgba(0,0,0,0)", showframe=False, showcoastlines=False, showland=True, landcolor="rgba(148,163,184,0.08)",
        showocean=False, showcountries=True, countrycolor="rgba(6,8,13,0.9)", countrywidth=0.6,
        projection_type="natural earth", lataxis_range=[-58, 85]))
    return fig


def build_var_chart(var_hist, var_param, cvar):
    vals = [abs(var_hist), abs(var_param), abs(cvar)]
    fig = go.Figure(go.Bar(
        x=["Hist. VaR", "Param. VaR", "CVaR"], y=vals,
        marker={"color": [C["cyan"], C["violet"], C["rose"]], "line": {"width": 0}, "cornerradius": 6},
        text=[f"{v:.2f}%" for v in vals], textposition="outside",
        textfont={"color": C["text"], "size": 11, "family": FONT_MONO},
        hovertemplate="%{x}: %{y:.2f}%<extra></extra>"))
    theme(fig, 240, margin=dict(t=24, b=28, l=40, r=8), pct_y=True)
    fig.update_layout(bargap=0.45, yaxis_range=[0, max(vals) * 1.3 if vals else 1])
    return fig


def build_monthly_heatmap(cum_returns_dict):
    """Monthly returns heatmap, built from daily returns derived from the cumulative series."""
    try:
        s = pd.Series(cum_returns_dict)
        s.index = pd.to_datetime(s.index)
        daily = s.sort_index().pct_change().dropna()
        monthly = daily.resample("ME").apply(lambda x: (1 + x).prod() - 1) * 100
        df = pd.DataFrame({"year": monthly.index.year, "month": monthly.index.month, "ret": monthly.values})
        pivot = df.pivot(index="year", columns="month", values="ret")
        names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        lim = float(np.nanmax(np.abs(pivot.values))) or 1
        fig = go.Figure(go.Heatmap(
            z=pivot.values, x=[names[c - 1] for c in pivot.columns], y=pivot.index.astype(str),
            colorscale=[[0, C["rose"]], [0.5, "#111827"], [1, C["mint"]]], zmid=0, zmin=-lim, zmax=lim, xgap=3, ygap=3,
            text=[[f"{v:.1f}" if not np.isnan(v) else "" for v in row] for row in pivot.values],
            texttemplate="%{text}", textfont={"size": 10, "family": FONT_MONO, "color": C["text"]}, showscale=False,
            hovertemplate="<b>%{x} %{y}</b>: %{z:.2f}%<extra></extra>"))
        theme(fig, 240, margin=dict(t=6, b=28, l=44, r=6))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        return fig
    except Exception:
        return None


def build_waterfall(individual_metrics):
    tickers = list(individual_metrics.keys())
    contribs = [individual_metrics[t]["annualized_return"] * individual_metrics[t]["weight"] / 100 for t in tickers]
    y = contribs + [sum(contribs)]
    fig = go.Figure(go.Waterfall(
        x=tickers + ["Portfolio"], y=y, measure=["relative"] * len(tickers) + ["total"],
        connector={"line": {"color": "rgba(148,163,184,0.25)", "width": 1, "dash": "dot"}},
        decreasing={"marker": {"color": C["rose"]}}, increasing={"marker": {"color": C["mint"]}}, totals={"marker": {"color": C["violet"]}},
        text=[f"{v:+.1f}%" for v in y], textfont={"size": 10, "family": FONT_MONO, "color": C["text"]}, textposition="outside", cliponaxis=False,
        hovertemplate="%{x}: %{y:.2f}%<extra></extra>"))
    theme(fig, 240, margin=dict(t=30, b=28, l=40, r=8), pct_y=True)
    return fig


def build_radar(individual_metrics):
    tickers = list(individual_metrics.keys())[:6]
    cats = ["Return", "Sharpe", "Low vol", "Weight", "Ret / vol"]
    ret = [individual_metrics[t]["annualized_return"] for t in tickers]
    shp = [individual_metrics[t]["sharpe"] for t in tickers]
    vol = [individual_metrics[t]["volatility"] for t in tickers]
    wt = [individual_metrics[t]["weight"] for t in tickers]
    rv = [r / v if v else 0 for r, v in zip(ret, vol)]

    def norm(vals, invert=False):
        mn, mx = min(vals), max(vals)
        if mx == mn:
            return [50] * len(vals)
        n = [(v - mn) / (mx - mn) * 100 for v in vals]
        return [100 - v for v in n] if invert else n

    cols = [norm(ret), norm(shp), norm(vol, invert=True), norm(wt), norm(rv)]
    fig = go.Figure()
    for i, t in enumerate(tickers):
        vals = [c[i] for c in cols]
        col = CHART_COLORS[i % len(CHART_COLORS)]
        fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=cats + [cats[0]], fill="toself",
                                      fillcolor=f"rgba({int(col[1:3], 16)},{int(col[3:5], 16)},{int(col[5:7], 16)},0.10)",
                                      line={"color": col, "width": 1.6}, name=t))
    theme(fig, 260, margin=dict(t=22, b=22, l=30, r=30), legend=True)
    fig.update_layout(
        polar={"bgcolor": "rgba(0,0,0,0)",
               "radialaxis": {"visible": True, "range": [0, 100], "showticklabels": False, "gridcolor": GRID, "linecolor": "rgba(0,0,0,0)"},
               "angularaxis": {"tickfont": {"size": 10, "color": C["muted"], "family": FONT_SANS}, "gridcolor": GRID, "linecolor": GRID}},
        legend={"font": {"size": 10, "color": C["muted"]}, "bgcolor": "rgba(0,0,0,0)", "orientation": "h", "y": -0.08, "x": 0.5, "xanchor": "center"})
    return fig


def build_rolling_vol(cum_returns_dict):
    try:
        s = pd.Series(cum_returns_dict).sort_index()
        rv = (s.pct_change().dropna().rolling(30).std() * np.sqrt(252) * 100).dropna()
        fig = go.Figure(go.Scatter(
            x=list(rv.index), y=list(rv.values), mode="lines",
            line={"color": C["violet"], "width": 2, "shape": "spline", "smoothing": 0.6},
            fill="tozeroy", fillcolor="rgba(167,139,250,0.10)",
            hovertemplate="<b>%{x}</b><br>Vol %{y:.2f}%<extra></extra>"))
        theme(fig, 210, pct_y=True)
        fig.update_layout(hovermode="x unified")
        return fig
    except Exception:
        return None


def build_cum(cum_returns_dict):
    s = pd.Series(cum_returns_dict).sort_index()
    pct = (s - 1) * 100
    up = pct.iloc[-1] >= 0 if len(pct) else True
    col, fill = (C["cyan"], "rgba(34,211,238,0.10)") if up else (C["rose"], "rgba(251,113,133,0.10)")
    fig = go.Figure(go.Scatter(
        x=list(pct.index), y=list(pct.values), mode="lines", fill="tozeroy", fillcolor=fill,
        line={"color": col, "width": 2.4, "shape": "spline", "smoothing": 0.5},
        hovertemplate="<b>%{x}</b><br>%{y:+.2f}%<extra></extra>"))
    theme(fig, 260, pct_y=True)
    fig.update_layout(hovermode="x unified")
    fig.add_hline(y=0, line={"color": "rgba(148,163,184,0.25)", "width": 1, "dash": "dot"})
    return fig


def build_sector(sec_d):
    fig = go.Figure(go.Pie(
        labels=list(sec_d.keys()), values=list(sec_d.values()), hole=0.68, sort=True,
        marker={"colors": CHART_COLORS, "line": {"color": "#0b0f18", "width": 3}},
        textinfo="none", hovertemplate="%{label}: %{value:.1f}%<extra></extra>"))
    top = max(sec_d, key=sec_d.get) if sec_d else ""
    theme(fig, 260, margin=dict(t=6, b=6, l=6, r=6), legend=True)
    fig.update_layout(
        legend={"font": {"color": C["muted"], "size": 10, "family": FONT_SANS}, "bgcolor": "rgba(0,0,0,0)", "orientation": "h", "y": -0.05, "x": 0.5, "xanchor": "center"},
        annotations=[{"text": f"<b>{sec_d.get(top, 0):.0f}%</b><br><span style='font-size:10px;color:{C['dim']}'>{top}</span>",
                      "showarrow": False, "font": {"size": 20, "color": C["text"], "family": FONT_MONO}, "y": 0.55}])
    return fig


def build_corr(corr):
    ct = list(corr.keys())
    z = [[corr[a].get(b, 0) for b in ct] for a in ct]
    fig = go.Figure(go.Heatmap(
        z=z, x=ct, y=ct, colorscale=[[0, C["rose"]], [0.5, "#111827"], [1, C["cyan"]]], zmid=0, zmin=-1, zmax=1, xgap=3, ygap=3,
        text=[[f"{v:.2f}" for v in row] for row in z], texttemplate="%{text}",
        textfont={"size": 10, "color": C["text"], "family": FONT_MONO}, showscale=False,
        hovertemplate="%{x} / %{y}: %{z:.2f}<extra></extra>"))
    theme(fig, 260, margin=dict(t=4, b=24, l=48, r=4))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig


# ---------------------------------------------------------------- analysis
@app.callback(
    Output("results", "children"), Output("err-msg", "children"), Output("portfolio-store", "data"), Output("topbar-sub", "children"),
    Input("analyze-btn", "n_clicks"),
    [State({"type": "ticker", "index": i}, "value") for i in range(N_ROWS)] +
    [State({"type": "weight", "index": i}, "value") for i in range(N_ROWS)] +
    [State("period-store", "value")],
    prevent_initial_call=True,
)
def analyze(_, *args):
    tickers_raw, weights_raw, period = list(args[:N_ROWS]), list(args[N_ROWS:N_ROWS * 2]), args[N_ROWS * 2] or "1y"
    pairs = []
    for t, w in zip(tickers_raw, weights_raw):
        try:
            w = float(w)
        except (TypeError, ValueError):
            continue
        if t and str(t).strip() and w > 0:
            pairs.append((str(t).strip().upper(), w))
    if len(pairs) < 2:
        return no_update, "Add at least 2 tickers with weights.", no_update, no_update
    tickers = [p[0] for p in pairs]
    total = sum(p[1] for p in pairs)
    weights = [p[1] / total for p in pairs]
    try:
        resp = requests.post(f"{API_URL}/analyze", json={"tickers": tickers, "weights": weights, "period": period}, timeout=120)
        if resp.status_code != 200:
            return no_update, resp.json().get("detail", "Analysis failed"), no_update, no_update
        data = resp.json()
    except requests.exceptions.ConnectionError:
        return no_update, "API is offline. Start the FastAPI service.", no_update, no_update
    except Exception as e:
        return no_update, str(e), no_update, no_update

    m = data["metrics"]
    ai = data["ai_insights"]
    rc = RISK_COLORS.get(ai["risk_label"], C["amber"])
    period_lbl = {"6mo": "6M", "1y": "1Y", "2y": "2Y", "5y": "5Y"}.get(period, period)

    def sign_c(v, good_if_pos=True):
        return (C["mint"] if v > 0 else C["rose"]) if good_if_pos else (C["rose"] if v > 0 else C["mint"])

    def mcard(lbl, val, sfx, color, badge, icon, idx, sub):
        return html.Div([
            html.Div([html.Span(icon, className="m-ic"), html.Span(lbl, className="m-lbl"), html.Span(badge, className="m-badge")], className="m-top"),
            html.Div(f"{fmt(val)}{sfx}", className="m-val"),
            html.Div(sub, className="m-sub"),
        ], className=f"m-card fi d{idx}", style={"--accent": color})

    sc = C["mint"] if m["sharpe_ratio"] > 1 else C["amber"] if m["sharpe_ratio"] > 0.5 else C["rose"]
    soc = C["mint"] if m["sortino_ratio"] > 1.5 else C["amber"] if m["sortino_ratio"] > 0.75 else C["rose"]
    dc = C["rose"] if m["max_drawdown"] < -20 else C["amber"] if m["max_drawdown"] < -10 else C["mint"]
    bcol = C["rose"] if m["beta"] > 1.3 else C["amber"] if m["beta"] > 1 else C["blue"]

    metrics = html.Div([
        mcard("Annual return", m["annualized_return"], "%", sign_c(m["annualized_return"]), period_lbl, "↗", 1, "Annualised"),
        mcard("Volatility", m["volatility"], "%", C["amber"], "ANN", "σ", 1, "Annualised std. dev."),
        mcard("Sharpe ratio", m["sharpe_ratio"], "", sc, "RF 5%", "S", 2, "Return per unit of risk"),
        mcard("Sortino", m["sortino_ratio"], "", soc, "DOWN", "▿", 2, "Downside-adjusted"),
        mcard("Max drawdown", m["max_drawdown"], "%", dc, "P→T", "↘", 3, "Worst peak to trough"),
        mcard("Beta", m["beta"], "", bcol, "SPY", "β", 3, "Sensitivity to market"),
        mcard("95% VaR", m["var_95"]["var_historical"], "%", C["rose"], "HIST", "!", 4, "Daily loss, 1-in-20 days"),
        mcard("CVaR", m["var_95"]["cvar"], "%", C["pink"], "95%", "∑", 4, "Avg loss beyond VaR"),
    ], className="m-grid")

    rr_ratio = round(abs(m["annualized_return"] / m["max_drawdown"]), 2) if m["max_drawdown"] else 0
    tail_ratio = round(abs(m["var_95"]["var_historical"] / m["var_95"]["cvar"]), 2) if m["var_95"]["cvar"] else 0
    diversification = max(0, min(100, round(100 - max(data["sector_exposure"].values())))) if data["sector_exposure"] else 0

    def dstat(label, value, sub, color):
        return html.Div([html.Div(label, className="d-lbl"), html.Div(str(value), className="d-val"), html.Div(sub, className="d-sub")],
                        className="d-stat", style={"--accent": color})

    def ai_card(title, txt, color):
        return html.Div([html.Div([html.I(), title], className="ai-sub"), html.Div(txt, className="ai-txt")], className="ai-card", style={"--accent": color})

    insight = html.Div([
        sh("Risk intelligence", C["violet"], "Generated by Nova Lite"),
        html.Div([
            html.Div([
                dcc.Graph(figure=mk_gauge(ai["risk_score"], ai["risk_label"]), config={"displayModeBar": False}, style={"height": "165px", "width": "220px"}),
                html.Div(ai["risk_label"], className="risk-label"),
            ], className="gauge-box", style={"--rc": rc}),
            html.Div([
                dstat("Risk / reward", rr_ratio, "Return ÷ max drawdown", C["mint"] if rr_ratio > 3 else C["amber"] if rr_ratio > 1.5 else C["rose"]),
                dstat("Tail ratio", tail_ratio, "VaR ÷ CVaR", C["violet"]),
                dstat("Diversification", f"{diversification}%", "Outside top sector", C["mint"] if diversification > 60 else C["amber"] if diversification > 30 else C["rose"]),
                dstat("Holdings", len(data.get("tickers", tickers)), "Active positions", C["blue"]),
            ], className="d-grid"),
        ], className="risk-row"),
        html.Div([
            ai_card("Summary", ai["risk_summary"], C["cyan"]),
            ai_card("Sector concentration", ai["sector_insights"], C["amber"]),
            ai_card("Correlation risk", ai["correlation_insights"], C["violet"]),
        ], className="ai-grid"),
    ], className="qp fi d2")

    recs = html.Div([
        sh("Recommendations", C["mint"], f"{len(ai['recommendations'])} actions"),
        html.Div([html.Div([html.Div(str(i + 1), className="rec-n"), html.Div(r, className="rec-t")], className="rec-card")
                  for i, r in enumerate(ai["recommendations"])], className="rec-grid"),
    ], className="qp fi d3")

    cum_s = pd.Series(data["cumulative_returns"]).sort_index()
    total_ret = (cum_s.iloc[-1] - 1) * 100 if len(cum_s) else 0
    row1 = html.Div([
        html.Div([sh("Cumulative returns", C["cyan"], f"{total_ret:+.1f}% over {period_lbl}"), graph(build_cum(data["cumulative_returns"]))], className="qp fi d4"),
        html.Div([sh("Sector exposure", C["amber"]), graph(build_sector(data["sector_exposure"]))], className="qp fi d4"),
    ], className="grid g-21")

    row2 = html.Div([
        html.Div([sh("Correlation matrix", C["cyan"]), graph(build_corr(data["correlation_matrix"]))], className="qp fi d5"),
        html.Div([sh("VaR breakdown", C["rose"], "95% daily"), graph(build_var_chart(m["var_95"]["var_historical"], m["var_95"]["var_parametric"], m["var_95"]["cvar"]))], className="qp fi d5"),
        html.Div([sh("Holdings radar", C["violet"], "Normalised"), graph(build_radar(data["individual_metrics"]))], className="qp fi d5"),
    ], className="grid g-3")

    wf, mh, rv = build_waterfall(data["individual_metrics"]), build_monthly_heatmap(data["cumulative_returns"]), build_rolling_vol(data["cumulative_returns"])
    row3 = html.Div([
        html.Div([sh("Return contribution", C["mint"], "Weight × return"), graph(wf)], className="qp fi d6"),
        html.Div([sh("Monthly returns", C["blue"], "%"), graph(mh)], className="qp fi d6") if mh else None,
    ], className="grid g-2")
    vol_panel = html.Div([sh("Rolling 30-day volatility", C["violet"], "Annualised"), graph(rv)], className="qp fi d6") if rv else None

    world = html.Div([sh("Geographic revenue exposure", C["cyan"], "Revenue-weighted"), graph(build_geo(tickers, weights))], className="qp fi d7")

    max_w = max((v["weight"] for v in data["individual_metrics"].values()), default=1) or 1
    holdings = html.Div([
        sh("Holdings breakdown", C["blue"]),
        html.Table([
            html.Thead(html.Tr([html.Th(h) for h in ["Ticker", "Weight", "Ann. return", "Volatility", "Sharpe", "Contribution"]])),
            html.Tbody([html.Tr([
                html.Td(html.Span([html.I(style={"background": CHART_COLORS[i % len(CHART_COLORS)]}), t], className="tc")),
                html.Td(html.Div([html.Span(f"{fmt(v['weight'], 1)}%"), html.Div(html.Span(style={"width": f"{v['weight'] / max_w * 100}%"}))], className="wbar")),
                html.Td(f"{fmt(v['annualized_return'])}%", style={"color": sign_c(v["annualized_return"])}),
                html.Td(f"{fmt(v['volatility'])}%", style={"color": C["amber"]}),
                html.Td(f"{fmt(v['sharpe'])}", style={"color": sign_c(v["sharpe"])}),
                html.Td(f"{v['weight'] * v['annualized_return'] / 100:+.2f}%", style={"color": C["text"]}),
            ]) for i, (t, v) in enumerate(data["individual_metrics"].items())]),
        ], className="q-tbl"),
    ], className="qp fi d8")

    port_news, macro_news = data.get("news", []), data.get("macro_news", [])
    news_items = []
    def junk(a):
        # Tavily sometimes returns Yahoo quote-comparison pages: ticker lists, not articles
        t = a.get("title", "")
        return t.count(",") >= 4 or "Quote Comparison" in t or not t.strip()

    port_news = [a for a in port_news if not junk(a)]
    macro_news = [a for a in macro_news if not junk(a)]
    for i, a in enumerate((port_news + macro_news)[:8]):
        is_port = i < len(port_news)
        tc, bg = (C["cyan"], "rgba(34,211,238,0.10)") if is_port else (C["violet"], "rgba(167,139,250,0.12)")
        src = urlparse(a.get("url", "")).netloc.replace("www.", "")
        snippet = a.get("content", "")
        news_items.append(html.A([
            html.Div([html.Span("PORTFOLIO" if is_port else "MACRO", className="news-tag", style={"color": tc, "background": bg}),
                      html.Span(src, className="news-src")], className="news-top"),
            html.Div(a.get("title", ""), className="news-title"),
            html.Div(snippet[:180] + ("..." if len(snippet) > 180 else ""), className="news-snippet"),
        ], href=a.get("url", "#"), target="_blank", rel="noopener", className="news-item"))

    news = html.Div([
        sh("Market intelligence", C["pink"], "via Tavily"),
        html.Div(news_items, className="news-grid") if news_items else html.Div("No news available right now.", className="ai-txt"),
    ], className="qp fi d9")

    sub = f"{len(tickers)} holdings · {period_lbl} lookback · {ai['risk_label'].lower()}"
    return html.Div([metrics, insight, recs, row1, row2, row3, vol_panel, world, holdings, news]), "", data, sub


# ---------------------------------------------------------------- chat
@app.callback(Output("chat-context", "children"), Output("chat-context", "className"), Input("portfolio-store", "data"))
def chat_context(data):
    if not data:
        return [html.Span(className="ctx-dot"), html.Span("No portfolio in context yet")], "ctx"
    ai = data.get("ai_insights", {})
    tks = data.get("tickers", [])
    label = ", ".join(tks[:4]) + (f" +{len(tks) - 4}" if len(tks) > 4 else "")
    return [html.Span(className="ctx-dot"), html.Span(["Context: ", html.B(label), f" · risk {ai.get('risk_score', '?')}/100"])], "ctx on"


def bot_bubble(children):
    return html.Div([
        html.Div(html.Img(src=SPARK, alt=""), className="bot-av"),
        html.Div([html.Div("Nova", className="b-lbl"), children], className="b-bot"),
    ], className="bw-bot")


HINTS = {"hint-1": "Why is my Sharpe ratio low?", "hint-2": "How can I reduce my portfolio beta?",
         "hint-3": "Am I overexposed to any sector?", "hint-4": "Give me rebalancing tips for this portfolio"}


# STEP 1: show the user bubble and typing indicator right away
@app.callback(
    Output("chat-messages", "children"), Output("chat-store", "data"), Output("chat-input", "value"),
    Input("chat-send", "n_clicks"), Input("chat-input", "n_submit"),
    Input("hint-1", "n_clicks"), Input("hint-2", "n_clicks"), Input("hint-3", "n_clicks"), Input("hint-4", "n_clicks"),
    State("chat-input", "value"), State("chat-messages", "children"), State("chat-store", "data"),
    prevent_initial_call=True,
)
def chat_step1(_s, _n, _h1, _h2, _h3, _h4, question, history, store):
    trig = ctx.triggered_id
    if trig in HINTS:
        if not ctx.triggered[0]["value"]:
            return no_update, no_update, no_update
        question = HINTS[trig]
    if not question or not question.strip():
        return no_update, no_update, no_update
    history = history or []
    user_bubble = html.Div(html.Div(question, className="b-user"), className="bw-user")
    thinking = html.Div([
        html.Div(html.Img(src=SPARK, alt=""), className="bot-av"),
        html.Div([html.Div("Nova", className="b-lbl"), html.Div([html.Span(), html.Span(), html.Span()], className="typing")], className="b-bot"),
    ], className="bw-bot", id="thinking-bubble")
    return history + [user_bubble, thinking], (store or []) + [question], ""


# STEP 2: swap the typing indicator for the real answer
@app.callback(
    Output("chat-messages", "children", allow_duplicate=True),
    Input("chat-store", "data"),
    State("chat-messages", "children"), State("portfolio-store", "data"),
    prevent_initial_call=True,
)
def chat_step2(store, history, portfolio_data):
    if not store:
        return no_update
    question = store[-1]
    history = history or []

    if not portfolio_data:
        answer = "Run a portfolio analysis first, then I can answer with your actual numbers."
    else:
        try:
            m = portfolio_data.get("metrics", {})
            ai = portfolio_data.get("ai_insights", {})
            prompt = f"""You are a portfolio risk analyst. Answer concisely using specific numbers.
Portfolio: {portfolio_data.get('tickers', [])}
Return: {m.get('annualized_return')}% | Vol: {m.get('volatility')}% | Sharpe: {m.get('sharpe_ratio')} | Beta: {m.get('beta')}
Max DD: {m.get('max_drawdown')}% | VaR: {m.get('var_95', {}).get('var_historical')}%
Risk: {ai.get('risk_score')}/100 ({ai.get('risk_label')})
Sectors: {portfolio_data.get('sector_exposure', {})}
Question: {question}
Answer in 2-3 sentences with specific numbers. You may use **bold** for key figures."""
            import boto3
            from dotenv import load_dotenv
            load_dotenv()
            client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"),
                                  aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))
            resp = client.invoke_model(
                modelId="amazon.nova-lite-v1:0",
                body=json.dumps({"messages": [{"role": "user", "content": [{"text": prompt}]}], "inferenceConfig": {"max_new_tokens": 256, "temperature": 0.3}}),
                contentType="application/json", accept="application/json")
            answer = json.loads(resp["body"].read())["output"]["message"]["content"][0]["text"]
        except Exception as e:
            answer = f"Something went wrong: `{e}`"

    msgs = [x for x in history if not (isinstance(x, dict) and x.get("props", {}).get("id") == "thinking-bubble")]
    return msgs + [bot_bubble(dcc.Markdown(answer, className="md"))]


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8050))
    debug = os.getenv("RAILWAY_ENVIRONMENT") is None
    app.run(debug=debug, host="0.0.0.0", port=port)
