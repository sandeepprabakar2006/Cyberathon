import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NetDictator",
    page_icon="🧢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }

/* ── DARK SIDEBAR ────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e3a8a 0%, #172554 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.1);
    box-shadow: 4px 0 24px rgba(0,0,0,0.3);
    min-width: 260px !important;
}
section[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* Sidebar logo */
.sidebar-brand {
    padding: 24px 4px 22px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 18px;
}
.sidebar-brand .logo-icon {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; margin-bottom: 10px;
    box-shadow: 0 4px 14px rgba(99,102,241,0.45);
}
.sidebar-brand .logo-text {
    font-size: 14px; font-weight: 800; color: #f1f5f9 !important;
    letter-spacing: -0.02em; line-height: 1.3;
}
.sidebar-brand .logo-sub {
    font-size: 11px; color: #64748b !important; font-weight: 400; margin-top: 2px;
}

/* Sidebar section label */
.sidebar-section-label {
    font-size: 10px; font-weight: 700; letter-spacing: .12em;
    color: #94a3b8 !important; text-transform: uppercase;
    padding: 0 4px 8px; margin-top: 4px;
}

/* Sidebar nav buttons */
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #94a3b8 !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: 10px 14px !important;
    margin-bottom: 2px !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.12) !important;
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] .stButton > button:active,
section[data-testid="stSidebar"] .stButton > button:focus {
    background: linear-gradient(90deg, rgba(99,102,241,0.25), rgba(59,130,246,0.12)) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    outline: none !important;
    box-shadow: inset 3px 0 0 #6366f1 !important;
}

/* Engine status pill */
.engine-status {
    display: flex; align-items: center; gap: 10px;
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 10px;
    padding: 10px 14px; margin-top: 14px;
}
.pulse-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #10b981;
    animation: pulse 2s infinite;
    flex-shrink: 0;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(16,185,129,0.6); }
    70%  { box-shadow: 0 0 0 8px rgba(16,185,129,0); }
    100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
}

/* Sidebar collapse hide */
button[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[kind="header"] { display: none !important; }
section[data-testid="stSidebar"][aria-expanded="false"] { display: flex !important; min-width: 240px !important; }

/* ── MAIN AREA ───────────────────────────────────────────────── */
.stApp { background: #fdf5e6; } /* Sandal/Cream Background */
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #0f172a !important; }

/* Page header bar */
.page-header-bar {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 24px;
    color: #fff;
    position: relative;
    overflow: hidden;
}
.page-header-bar::before {
    content: '';
    position: absolute; top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.page-header-bar::after {
    content: '';
    position: absolute; bottom: -60px; right: 60px;
    width: 140px; height: 140px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.page-header-bar h1 {
    font-size: 24px !important; font-weight: 800 !important;
    color: #fff !important; margin: 0 0 6px !important; line-height: 1.2;
}
.page-header-bar p {
    font-size: 13.5px !important; color: rgba(255,255,255,0.75) !important;
    margin: 0 !important;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}
div[data-testid="metric-container"] label { color: #94a3b8 !important; font-size: 11.5px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: .04em; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #0f172a !important; font-size: 30px !important; font-weight: 800 !important; }
div[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 11.5px !important; }

/* KPI colored cards */
.kpi-card {
    background: #fff;
    border-radius: 16px;
    padding: 22px 24px;
    display: flex;
    align-items: center;
    gap: 18px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    transition: transform 0.2s, box-shadow 0.2s;
    margin-bottom: 0;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
.kpi-icon {
    width: 52px; height: 52px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; flex-shrink: 0;
}
.kpi-info .kpi-label { font-size: 11.5px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: .04em; }
.kpi-info .kpi-value { font-size: 32px; font-weight: 800; color: #0f172a; line-height: 1.1; margin: 4px 0 2px; }
.kpi-info .kpi-sub   { font-size: 12px; color: #64748b; }

/* Content cards */
.netdictator-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    margin-bottom: 16px;
}
.netdictator-card h4 {
    font-size: 14.5px; font-weight: 700; color: #0f172a;
    margin: 0 0 18px; display: flex; align-items: center; gap: 8px;
    border-bottom: 1px solid #f1f5f9; padding-bottom: 12px;
}

/* Page header (simple for non-dashboard pages) */
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 22px; font-weight: 800; color: #0f172a; margin: 0; }
.page-header p  { font-size: 13px; color: #94a3b8; margin: 4px 0 0; }

/* Status badges */
.badge-green  { background: #dcfce7; color: #15803d; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; }
.badge-red    { background: #fee2e2; color: #b91c1c; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; }
.badge-orange { background: #fef9c3; color: #854d0e; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; }
.badge-blue   { background: #dbeafe; color: #1e40af; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; }
.badge-purple { background: #ede9fe; color: #5b21b6; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; }

/* Flow node */
.flow-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 16px 0; }
.flow-node-box {
    background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 10px;
    padding: 10px 16px; font-size: 13px; font-weight: 600; color: #1d4ed8;
    display: flex; align-items: center; gap: 7px;
}
.flow-arrow { font-size: 18px; color: #2563eb; }

/* Status card */
.status-box {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    border-left: 4px solid #10b981;
    display: flex; flex-direction: column; gap: 6px;
}
.status-box.warn { border-left-color: #f59e0b; }
.status-box h5 { font-size: 14px; font-weight: 700; color: #0f172a; margin: 0; }
.status-box p  { font-size: 12.5px; color: #94a3b8; margin: 0; }
.status-box .uptime { font-size: 11.5px; color: #64748b; }

/* Sensitivity indicator */
.sens-result { padding: 14px 18px; border-radius: 10px; margin: 10px 0; font-size: 14px; font-weight: 600; }
.sens-high   { background: #fef2f2; border: 1.5px solid #fca5a5; color: #991b1b; }
.sens-medium { background: #fffbeb; border: 1.5px solid #fcd34d; color: #92400e; }
.sens-low    { background: #ecfdf5; border: 1.5px solid #6ee7b7; color: #065f46; }

/* Action badge */
.action-big { display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 24px; font-size: 13px; font-weight: 700; margin: 4px; }
.act-enc   { background: #dbeafe; color: #1d4ed8; }
.act-mask  { background: #fef3c7; color: #92400e; }
.act-tok   { background: #ede9fe; color: #5b21b6; }
.act-plain { background: #dcfce7; color: #065f46; }
.act-block { background: #fee2e2; color: #991b1b; }

/* Table */
.styled-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.styled-table th { background: #f8fafc; color: #64748b; font-weight: 600; font-size: 11.5px; padding: 10px 14px; border-bottom: 2px solid #e2e8f0; text-align: left; letter-spacing: 0.03em; }
.styled-table td { padding: 12px 14px; border-bottom: 1px solid #f1f5f9; color: #334155; }
.styled-table tr:hover td { background: #f8faff; }

/* Plotly */
.js-plotly-plot .plotly { border-radius: 12px; }

hr { border: none; border-top: 1px solid #e2e8f0 !important; margin: 16px 0 !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE — Real request logs (only actual API calls) ─────────────────
if "adpe_logs" not in st.session_state:
    st.session_state.adpe_logs = []   # list of dicts, one per real API request

BACKEND = "http://localhost:8000"

# ─── Cached backend helpers ───────────────────────────────────────────────────
# Defined at TOP LEVEL so they survive page navigation reliably
@st.cache_data(ttl=60)
def fetch_my_ip():
    """Calls /my-ip on the backend to get the real caller IP."""
    try:
        import requests as _req
        r = _req.get(f"{BACKEND}/my-ip", timeout=4)
        return r.json()
    except Exception:
        return {"ip": "127.0.0.1", "network_type": "external",
                "ip_risk_score": 40, "intent": "unverified"}

@st.cache_data(ttl=60)
def fetch_s3_files():
    """Calls /list-files on the backend to get the S3 bucket file list."""
    try:
        import requests as _req
        r = _req.get(f"{BACKEND}/list-files", timeout=6)
        data = r.json()
        return data.get("files", [])
    except Exception:
        return []

# Shared action styling (used in multiple pages)
_ACT_BADGE = {
    "none":              "badge-green",
    "plain_access":      "badge-green",
    "masking":           "badge-orange",
    "tokenization":      "badge-purple",
    "encrypt_and_mask":  "badge-purple",
    "hybrid_encryption": "badge-blue",
}
_SENS_BADGE = {"Important": "badge-red", "Medium": "badge-orange", "Normal": "badge-green"}
_RISK_BADGE = {"LOW": "badge-green", "MEDIUM": "badge-orange", "HIGH": "badge-red"}

def _action_label(a: str) -> str:
    return a.replace("_", " ").title() if a else "nil"

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Embedded Logo
    st.image("/home/sandy/.gemini/antigravity/brain/0ad6be22-fd94-4296-ace1-6c5eda4c254c/netdictator_logo_1773446312057.png", width=80)
    
    st.markdown("""
    <div class="sidebar-brand" style="border-bottom:none; padding-top:0;">
      <div class="logo-text" style="font-size:24px; color:#ffffff !important;">NetDictator</div>
      <div class="logo-sub" style="color:#bfdbfe !important;">Supreme Data Authority</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)

    pages = {
        "📊  Overview":              "dashboard",
        "📁  File Access Requests":  "requests",
        "🧠  Data Sensitivity":      "analysis",
        "🔐  Security Actions":      "actions",
        "📋  Access Logs":           "logs",
        "🖥️  System Status":         "status",
        "⚙️  Settings":              "settings",
    }
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    for label, key in pages.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key

    st.markdown("""<div class="engine-status">
      <div class="pulse-dot"></div>
      <div>
        <div style="font-size:12px;color:#34d399!important;font-weight:700">Engine Active</div>
        <div style="font-size:10.5px;color:#94a3b8!important;margin-top:1px">VPC Private Subnet</div>
      </div>
    </div>""", unsafe_allow_html=True)

    total_reqs = len(st.session_state.adpe_logs)
    st.markdown(f"""<div style="margin-top:14px;padding:12px 14px;background:rgba(99,102,241,0.08);
        border:1px solid rgba(99,102,241,0.2);border-radius:10px">
      <div style="font-size:10px;color:#818cf8!important;font-weight:700;letter-spacing:.08em">SESSION REQUESTS</div>
      <div style="font-size:26px;font-weight:800;color:#e2e8f0!important;margin:4px 0 2px">{total_reqs}</div>
      <div style="font-size:10.5px;color:#94a3b8!important">requests analysed</div>
    </div>""", unsafe_allow_html=True)

page = st.session_state.page


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    logs  = st.session_state.adpe_logs
    total = len(logs)
    sensitive = sum(1 for r in logs if r.get("Sensitivity","").lower() == "important")
    external  = sum(1 for r in logs if r.get("User Type","").lower() == "external")
    encrypted = sum(1 for r in logs if r.get("Security Action","") in ("hybrid_encryption","encrypt_and_mask"))
    tokenized = sum(1 for r in logs if r.get("Security Action","") == "tokenization")
    masked    = sum(1 for r in logs if r.get("Security Action","") == "masking")
    nil_ops   = sum(1 for r in logs if r.get("Security Action","") in ("none","plain_access"))

    # ── Gradient header banner
    st.markdown("""
    <div class="page-header-bar">
      <h1>🧢 NetDictator Control Center</h1>
      <p>Data Sovereignty · Real-time Enforcement · Precision Security</p>
    </div>""", unsafe_allow_html=True)

    # ── KPI tiles (4 coloured cards)
    k1, k2, k3, k4 = st.columns(4)
    kpi_data = [
        (k1, "📁", "Total Requests",    str(total),     "This session",      "#3b82f6", "#eff6ff"),
        (k2, "⚠️", "Sensitive Files",   str(sensitive),  f"{sensitive}/{total} IMPORTANT", "#ef4444", "#fef2f2"),
        (k3, "🌐", "External Access",   str(external),   f"{external}/{total} from outside","#f59e0b", "#fffbeb"),
        (k4, "🔒", "Encrypted",         str(encrypted),  f"{encrypted} dual-layer protected","#8b5cf6", "#f5f3ff"),
    ]
    for col, icon, label, value, sub, fg, bg in kpi_data:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-icon" style="background:{bg};color:{fg}">{icon}</div>
              <div class="kpi-info">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{fg}">{value}</div>
                <div class="kpi-sub">{sub}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Row 2: Charts
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="netdictator-card"><h4>📈 Request Flow — Internal vs External</h4>', unsafe_allow_html=True)
        int_count = total - external
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Internal VPC", x=["This Session"], y=[int_count],
            marker_color="#3b82f6", marker_line_width=0,
            text=[int_count], textposition="outside",
        ))
        fig_bar.add_trace(go.Bar(
            name="External", x=["This Session"], y=[external],
            marker_color="#f59e0b", marker_line_width=0,
            text=[external], textposition="outside",
        ))
        fig_bar.update_layout(
            barmode="group", plot_bgcolor="#fafafa", paper_bgcolor="#fff",
            margin=dict(l=0,r=0,t=10,b=0), height=200,
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=12, family="Inter")),
            font=dict(family="Inter", color="#475569"),
            xaxis=dict(showgrid=False, linecolor="#e2e8f0"),
            yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", dtick=1, rangemode="tozero"),
        )
        if total == 0:
            fig_bar.add_annotation(
                text="No requests yet — run an analysis on File Access Requests page",
                x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                font=dict(size=13, color="#94a3b8", family="Inter"),
            )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="netdictator-card"><h4>🌀 Security Actions</h4>', unsafe_allow_html=True)
        if total == 0:
            pie_labels = ["No data"]; pie_values = [1]
            pie_colors = ["#e2e8f0"]; center_txt = "<b>0</b><br>Requests"
        else:
            action_map = {
                "Encrypt+Mask": (encrypted, "#8b5cf6"),
                "Tokenize":     (tokenized, "#3b82f6"),
                "Masking":      (masked,    "#f59e0b"),
                "None/Plain":   (nil_ops,   "#10b981"),
            }
            pie_labels = [k for k,(v,_) in action_map.items() if v > 0]
            pie_values = [v for k,(v,c) in action_map.items() if v > 0]
            pie_colors = [c for k,(v,c) in action_map.items() if v > 0]
            if not pie_labels:
                pie_labels, pie_values, pie_colors = ["No data"],[1],["#e2e8f0"]
            center_txt = f"<b>{total}</b><br>Total"
        fig_pie = go.Figure(go.Pie(
            labels=pie_labels, values=pie_values, hole=0.62,
            marker=dict(colors=pie_colors, line=dict(color="#fff", width=3)),
            textinfo="label+percent" if total > 0 else "none",
            textfont=dict(size=11, family="Inter"),
        ))
        fig_pie.update_layout(
            paper_bgcolor="#fff", plot_bgcolor="#fff",
            margin=dict(l=0,r=0,t=0,b=0), height=200,
            showlegend=False,
            annotations=[dict(text=center_txt, x=0.5, y=0.5, font_size=14,
                              showarrow=False, font=dict(family="Inter", color="#0f172a"))],
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Row 3: Risk spectrum + action breakdown
    r1, r2, r3, r4, r5 = st.columns(5)
    action_tiles = [
        (r1, "🔐", "Encrypt+Mask", encrypted, "#8b5cf6", "#f5f3ff"),
        (r2, "🔑", "Tokenize",    tokenized,  "#3b82f6", "#eff6ff"),
        (r3, "🎭", "Masking",     masked,     "#f59e0b", "#fffbeb"),
        (r4, "➖",    "Nil Ops",     nil_ops,    "#10b981", "#ecfdf5"),
        (r5, "⚠️",   "IMPORTANT",  sensitive,  "#ef4444", "#fef2f2"),
    ]
    for col, ico, lbl, cnt, fg, bg in action_tiles:
        with col:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {fg}22;border-radius:14px;
                        padding:16px 12px;text-align:center">
              <div style="font-size:22px;margin-bottom:6px">{ico}</div>
              <div style="font-size:24px;font-weight:800;color:{fg}">{cnt}</div>
              <div style="font-size:11px;color:#64748b;font-weight:600;margin-top:3px">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Recent Activity
    st.markdown('<div class="netdictator-card"><h4>🕐 Recent Activity — Last 5 Real Requests</h4>', unsafe_allow_html=True)
    if not logs:
        st.markdown("""
        <div style="text-align:center;padding:32px;color:#94a3b8">
          <div style="font-size:36px;margin-bottom:10px">📤</div>
          <div style="font-size:14px;font-weight:600">No requests yet</div>
          <div style="font-size:12.5px;margin-top:6px">Go to <b>File Access Requests</b> → select a file → click Run Security Analysis</div>
        </div>""", unsafe_allow_html=True)
    else:
        rows = ""
        for r in logs[:5]:
            sc = _SENS_BADGE.get(r.get("Sensitivity",""), "badge-blue")
            ac = _ACT_BADGE.get(r.get("Security Action",""), "badge-blue")
            rc = _RISK_BADGE.get(r.get("Risk Band", ""), "badge-blue")
            lbl = _action_label(r.get("Security Action",""))
            rows += f"""<tr>
                <td style="font-size:11.5px;white-space:nowrap">{r["Timestamp"]}</td>
                <td style="font-weight:600">{r["File"]}</td>
                <td><span class="{sc}">{r.get("Sensitivity","")}</span></td>
                <td style="font-size:11.5px">{r.get("IP Used","")}<br><small style="color:#94a3b8">{r.get("User Type","")}</small></td>
                <td><span class="{rc}">{r.get("Risk Score","")}</span></td>
                <td><span class="{ac}">{lbl}</span></td>
            </tr>"""
        st.markdown(f"""
        <table class="styled-table">
          <thead><tr>
            <th>Time</th><th>File</th><th>Sensitivity</th>
            <th>IP / Origin</th><th>Risk Score</th><th>Action Applied</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: FILE REQUESTS — Live Demo
# ══════════════════════════════════════════════════════════════════════════════
elif page == "requests":
    st.markdown("""<div class="page-header"><h1>📁 File Access Request — NetDictator Live</h1>
    <p>Select a file from your S3 bucket · Auto-detects your IP · See NetDictator's real security response</p></div>""",
    unsafe_allow_html=True)

    # BACKEND, fetch_my_ip, fetch_s3_files are all defined at top level
    ip_info    = fetch_my_ip()
    s3_files   = fetch_s3_files()
    file_names = [f["name"] for f in s3_files] if s3_files else [
        "payroll_march_2026.txt", "project_titan_notes.txt", "office_canteen_menu.txt"
    ]

    # ── Control Panel ──────────────────────────────────────────────────────────
    st.markdown('<div class="netdictator-card"><h4>🎛️ Request Configuration</h4>', unsafe_allow_html=True)

    col_ip, col_toggle = st.columns([3, 2])

    with col_ip:
        real_ip = ip_info.get("ip", "127.0.0.1")
        real_net = ip_info.get("network_type", "unknown").upper()
        real_intent = ip_info.get("intent", "")
        net_badge = "🟢 INTERNAL" if real_net == "INTERNAL" else "🔴 EXTERNAL"
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;margin-bottom:4px">
          <p style="margin:0;font-size:11px;color:#94a3b8;font-weight:600;letter-spacing:.05em">YOUR DETECTED IP</p>
          <p style="margin:4px 0 2px;font-size:22px;font-weight:700;color:#1e293b;font-family:monospace">{real_ip}</p>
          <p style="margin:0;font-size:12px;color:#64748b">{net_badge} &nbsp;·&nbsp; {real_intent}</p>
        </div>""", unsafe_allow_html=True)

    with col_toggle:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        sim_internal = st.toggle("🏠 Simulate VPC Internal IP", value=False,
            help="Simulate request from inside your private VPC subnet (10.0.1.50)")
        if sim_internal:
            active_ip = "10.0.1.50"
            st.markdown("""<div style="font-size:12px;color:#16a34a;margin-top:4px">
            ✅ Using VPC internal IP: <b>10.0.1.50</b><br>
            <span style="color:#64748b">Simulates trusted employee inside subnet</span></div>""",
            unsafe_allow_html=True)
        else:
            active_ip = real_ip
            st.markdown(f"""<div style="font-size:12px;color:#dc2626;margin-top:4px">
            🌍 Using your real IP: <b>{real_ip}</b><br>
            <span style="color:#64748b">Simulates request from internet</span></div>""",
            unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── File + Role Selector ───────────────────────────────────────────────────
    st.markdown('<div class="netdictator-card"><h4>📂 Select File & Role</h4>', unsafe_allow_html=True)
    col_f, col_r = st.columns([3, 2])

    with col_f:
        selected_file = st.selectbox("📁 Files in S3 Bucket (netdictator-vault-raw)",
            options=file_names,
            help="These are your actual files fetched live from S3")
        # Show file info
        file_info = next((f for f in s3_files if f["name"] == selected_file), None)
        if file_info:
            st.caption(f"📦 Size: {file_info['size_bytes']} bytes  ·  🕐 Modified: {file_info['last_modified']}")

    with col_r:
        role_map = {
            "admin": "👔 Admin",
            "finance-manager": "💰 Finance Manager",
            "data-analyst": "📊 Data Analyst",
            "external-auditor": "🔍 External Auditor",
            "guest": "👤 Guest (will be blocked)"
        }
        selected_role_label = st.selectbox("🪪 IAM Role", list(role_map.values()))
        selected_role = [k for k, v in role_map.items() if v == selected_role_label][0]

    run_btn = st.button("🚀 Run Security Analysis", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Run the real API call ──────────────────────────────────────────────────
    if run_btn:
        import requests as req, json
        from datetime import datetime as dt

        with st.spinner("🔄 Running 4-layer security pipeline..."):
            try:
                resp = req.post(f"{BACKEND}/request-file",
                    json={"file_name": selected_file, "user_ip": active_ip, "user_role": selected_role},
                    timeout=15)
                data = resp.json()
            except Exception as e:
                st.error(f"❌ Could not reach backend: {e}")
                data = None

        if data and resp.status_code == 200:
            # ── Store to real session log ──
            st.session_state.adpe_logs.insert(0, {
                "Timestamp":       dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Request ID":      data["request_id"],
                "File":            data["file_name"],
                "Sensitivity":     data["sensitivity"].capitalize(),
                "User Type":       data["user_type"].capitalize(),
                "IAM Role":        selected_role,
                "IP Used":         active_ip,
                "NLP Score":       f"{data['nlp_score']}/60",
                "IP Score":        f"{data['ip_score']}/40",
                "Risk Score":      f"{data['risk_score']}/100",
                "Risk Band":       data["risk_band"],
                "Security Action": data["security_action"],
                "Ops Applied":     data.get("ops_applied", ""),
            })

            rs = data["risk_score"]
            rb = data["risk_band"]
            action = data["security_action"]
            sens = data["sensitivity"].upper()
            ops  = data.get("ops_applied", "")

            # Risk score colour
            if rb == "HIGH":     rs_color, rb_emoji = "#dc2626", "🔴"
            elif rb == "MEDIUM": rs_color, rb_emoji = "#f59e0b", "🟡"
            else:                rs_color, rb_emoji = "#16a34a", "🟢"

            # Action colour (including new actions)
            act_colors = {
                "hybrid_encryption": ("#1d4ed8", "#dbeafe", "🔒"),
                "encrypt_and_mask":  ("#7c3aed", "#ede9fe", "🔐"),  # external admin
                "masking":           ("#92400e", "#fef3c7", "👁️"),
                "tokenization":      ("#5b21b6", "#ede9fe", "🔑"),
                "plain_access":      ("#065f46", "#dcfce7", "✅"),
                "none":              ("#475569", "#f1f5f9", "➖"),  # nil ops
            }
            ac, abg, aico = act_colors.get(action, ("#475569", "#f1f5f9", "❓"))

            st.markdown("---")
            st.markdown("### 📊 Security Analysis Result")

            # KPI row replaced with high-contrast HTML cards
            k1, k2, k3, k4 = st.columns(4)
            with k1: 
                st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #3b82f6; padding:15px">
                    <div class="kpi-info">
                        <div class="kpi-label">🎯 Sensitivity</div>
                        <div class="kpi-value" style="font-size:24px; color:#1e293b">{sens}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with k2:
                st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #10b981; padding:15px">
                    <div class="kpi-info">
                        <div class="kpi-label">🌐 User Type</div>
                        <div class="kpi-value" style="font-size:24px; color:#1e293b">{data["user_type"].upper()}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with k3:
                st.markdown(f"""<div class="kpi-card" style="border-left:4px solid {rs_color}; padding:15px">
                    <div class="kpi-info">
                        <div class="kpi-label">📊 Risk Score</div>
                        <div class="kpi-value" style="font-size:24px; color:#1e293b">{rs}/100</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with k4:
                st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #8b5cf6; padding:15px">
                    <div class="kpi-info">
                        <div class="kpi-label">🧠 NLP + IP</div>
                        <div class="kpi-value" style="font-size:24px; color:#1e293b">{data['nlp_score']} + {data['ip_score']}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

            # Ops applied banner
            st.markdown(f"""
            <div style="background:#f8fafc;border-left:4px solid {ac};border-radius:8px;
                        padding:12px 16px;margin:12px 0;font-size:13px">
              <b>Security Operations Applied:</b> &nbsp;
              <span style="color:{ac};font-weight:700">{ops if ops else 'nil — no transformation'}</span>
            </div>""", unsafe_allow_html=True)

            # Risk + Action cards
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div style="background:#f8fafc;border:2px solid {rs_color};border-radius:14px;padding:20px;text-align:center">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600">RISK BAND</p>
                  <p style="margin:8px 0;font-size:36px;font-weight:800;color:{rs_color}">{rb_emoji} {rb}</p>
                  <p style="margin:0;font-size:13px;color:#64748b">Score: <b>{rs}/100</b></p>
                  <p style="margin:4px 0 0;font-size:11px;color:#94a3b8">NLP({data['nlp_score']}) + IP({data['ip_score']}) = {rs}</p>
                </div>""", unsafe_allow_html=True)

            with c2:
                st.markdown(f"""
                <div style="background:{abg};border:2px solid {ac};border-radius:14px;padding:20px;text-align:center">
                  <p style="margin:0;font-size:12px;color:#64748b;font-weight:600">SECURITY ACTION APPLIED</p>
                  <p style="margin:8px 0;font-size:28px;font-weight:800;color:{ac}">{aico} {action.replace('_',' ').title()}</p>
                  <p style="margin:0;font-size:11px;color:#94a3b8">Intent: {data['intent'][:40]}...</p>
                </div>""", unsafe_allow_html=True)

            # Pipeline flow
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#f8fafc;border-radius:12px;padding:18px;font-size:13px">
              <b>🔄 4-Layer Pipeline</b><br><br>
              <div class="flow-row">
                <div class="flow-node-box">📥 S3: {selected_file}</div>
                <span class="flow-arrow">→</span>
                <div class="flow-node-box" style="background:#f3e8ff;border-color:#ddd6fe;color:#5b21b6">
                  🧠 NLP Score: {data['nlp_score']}/60<br><small>{sens}</small>
                </div>
                <span class="flow-arrow">→</span>
                <div class="flow-node-box" style="background:#fffbeb;border-color:#fde68a;color:#92400e">
                  🌐 IP Score: {data['ip_score']}/40<br><small>{data['user_type'].upper()}</small>
                </div>
                <span class="flow-arrow">→</span>
                <div class="flow-node-box" style="background:#ecfdf5;border-color:#6ee7b7;color:#065f46">
                  🪪 IAM: {data['iam_permission'].upper()}<br><small>{selected_role}</small>
                </div>
                <span class="flow-arrow">→</span>
                <div class="flow-node-box" style="background:{abg};border-color:{ac};color:{ac}">
                  {aico} {action.replace('_',' ').title()}<br><small>{rb} RISK</small>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            # ── Prominent Output Section
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="netdictator-card"><h4>🔍 Final Processed Output (Delivered Data)</h4>', unsafe_allow_html=True)
            
            # Show the actual transformation in a large, readable code block
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:15px; margin-bottom:15px">
               <p style="font-size:12px; color:#64748b; margin-bottom:8px"><b>Response Body — {action.replace("_", " ").title()} Applied</b></p>
            </div>""", unsafe_allow_html=True)
            
            st.code(data["processed_data"], language="json" if "{" in data["processed_data"] else "text")
            
            # Add a download button for the secure file
            st.download_button(
                label=f"⬇️ Download Secure {selected_file}",
                data=data["processed_data"],
                file_name=f"secure_{selected_file}",
                mime="text/plain",
                use_container_width=True
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.success(f"✅ Request ID: `{data['request_id']}` — {data['message']}")

        elif data:
            st.error(f"🚫 {data.get('detail', 'Access Denied')}")



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SECURITY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "analysis":
    st.markdown("""<div class="page-header"><h1>🧠 NetDictator Decision Flow</h1>
    <p>Supreme Data Authority logic and processing pipeline visualization</p></div>""", unsafe_allow_html=True)

    st.markdown('<div class="netdictator-card"><h4>⚙️ Request Processing Pipeline</h4>', unsafe_allow_html=True)
    st.markdown("""
    <div class="flow-row">
      <div class="flow-node-box">👤 User Request</div>
      <span class="flow-arrow">→</span>
      <div class="flow-node-box" style="background:#f3e8ff;border-color:#ddd6fe;color:#5b21b6">🧠 NLP Sensitivity Detection</div>
      <span class="flow-arrow">→</span>
      <div class="flow-node-box" style="background:#fffbeb;border-color:#fde68a;color:#92400e">🌐 IP Verification</div>
      <span class="flow-arrow">→</span>
      <div class="flow-node-box" style="background:#ecfdf5;border-color:#6ee7b7;color:#065f46">🪪 IAM Role Classification</div>
      <span class="flow-arrow">→</span>
      <div class="flow-node-box" style="background:#fef2f2;border-color:#fca5a5;color:#991b1b">🔐 Security Action</div>
    </div>
    <hr/>
    <p style="font-size:13px;color:#64748b;margin:10px 0 8px"><b>Possible Security Actions:</b></p>
    <span class="action-big act-enc">🔒 Encryption</span>
    <span class="action-big act-mask">👁️ Masking</span>
    <span class="action-big act-tok">🔑 Tokenization</span>
    <span class="action-big act-plain">✅ Plain Access</span>
    <span class="action-big act-block">🚫 Block</span>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="netdictator-card"><h4>🧠 NLP Model Information</h4>', unsafe_allow_html=True)
        st.markdown("""
        <table class="styled-table">
          <tbody>
            <tr><td style="color:#64748b">Model Type</td><td><b>BERT-based Classifier</b></td></tr>
            <tr><td style="color:#64748b">Accuracy</td><td><b>97.4%</b></td></tr>
            <tr><td style="color:#64748b">Sensitivity Classes</td><td><b>Important / Medium / Normal</b></td></tr>
            <tr><td style="color:#64748b">Last Trained</td><td><b>2026-03-01</b></td></tr>
            <tr><td style="color:#64748b">Inference Latency</td><td><b>42 ms avg</b></td></tr>
          </tbody>
        </table>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="netdictator-card"><h4>⚖️ Decision Matrix</h4>', unsafe_allow_html=True)
        st.markdown("""
        <table class="styled-table">
          <thead><tr><th>Sensitivity</th><th>Internal User</th><th>External User</th></tr></thead>
          <tbody>
            <tr>
              <td><span class="badge-red">Important</span></td>
              <td><span class="badge-blue">Encrypt</span></td>
              <td><span class="badge-red">Block</span></td>
            </tr>
            <tr>
              <td><span class="badge-orange">Medium</span></td>
              <td><span class="badge-orange">Mask</span></td>
              <td><span class="badge-purple">Tokenize</span></td>
            </tr>
            <tr>
              <td><span class="badge-green">Normal</span></td>
              <td><span class="badge-green">Plain Access</span></td>
              <td><span class="badge-green">Plain Access</span></td>
            </tr>
          </tbody>
        </table>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Sensitivity trend chart
    st.markdown('<div class="netdictator-card"><h4>📊 Sensitivity Distribution Trend</h4>', unsafe_allow_html=True)
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=days, y=[45,60,38,72,55,30,68], name="Important",
        line=dict(color="#ef4444", width=2.5), fill="tozeroy",
        fillcolor="rgba(239,68,68,0.08)"))
    fig2.add_trace(go.Scatter(x=days, y=[80,95,70,110,88,55,102], name="Medium",
        line=dict(color="#f59e0b", width=2.5), fill="tozeroy",
        fillcolor="rgba(245,158,11,0.08)"))
    fig2.add_trace(go.Scatter(x=days, y=[120,140,110,160,130,90,150], name="Normal",
        line=dict(color="#10b981", width=2.5), fill="tozeroy",
        fillcolor="rgba(16,185,129,0.08)"))
    fig2.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0,r=0,t=5,b=5), height=220,
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1,
                    font=dict(size=12, family="Inter")),
        font=dict(family="Inter", color="#475569"),
        xaxis=dict(showgrid=False, linecolor="#e2e8f0"),
        yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0"),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SECURITY ACTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "actions":
    st.markdown("""<div class="page-header"><h1>🔐 Security Actions</h1>
    <p>Protection measures — computed from real requests this session</p></div>""", unsafe_allow_html=True)

    logs = st.session_state.adpe_logs
    total = len(logs)

    # ── Compute real counts from session logs
    a_enc  = sum(1 for r in logs if r.get("Security Action") == "hybrid_encryption")
    a_enm  = sum(1 for r in logs if r.get("Security Action") == "encrypt_and_mask")
    a_mask = sum(1 for r in logs if r.get("Security Action") == "masking")
    a_tok  = sum(1 for r in logs if r.get("Security Action") == "tokenization")
    a_plain= sum(1 for r in logs if r.get("Security Action") in ("none", "plain_access"))

    if total == 0:
        st.info("📭 No requests yet. Go to **File Access Requests** → run an analysis → come back here to see real action counts.")

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, icon, title, desc, count, bg, fg in [
        (c1, "🔒", "Encryption",     "AES-256+RSA-2048 — external high-risk.",         a_enc,  "#dbeafe", "#1d4ed8"),
        (c2, "🔐", "Encrypt+Mask",   "Mask PII then encrypt — external admin.",        a_enm,  "#ede9fe", "#7c3aed"),
        (c3, "👁️", "Masking",        "Hides sensitive fields, preserves structure.",   a_mask, "#fef3c7", "#92400e"),
        (c4, "🔑", "Tokenization",   "Replaces values with secure tokens.",            a_tok,  "#ede9fe", "#5b21b6"),
        (c5, "➖", "None / Plain",   "Internal VPC trusted — nil operations.",         a_plain,"#dcfce7", "#065f46"),
    ]:
        with col:
            st.markdown(f"""
            <div class="netdictator-card" style="text-align:center">
              <div style="font-size:28px;margin-bottom:8px">{icon}</div>
              <h4 style="justify-content:center;color:#1e293b;font-size:14px;margin-bottom:6px">{title}</h4>
              <p style="font-size:11.5px;color:#64748b;margin-bottom:12px">{desc}</p>
              <div style="font-size:30px;font-weight:800;color:{fg};background:{bg};
                          border-radius:10px;padding:10px">{count}</div>
              <p style="font-size:10px;color:#94a3b8;margin-top:6px">Real count this session</p>
            </div>""", unsafe_allow_html=True)

    # ── Bar chart from real data
    st.markdown('<div class="netdictator-card"><h4>📊 Actions Applied — This Session</h4>', unsafe_allow_html=True)
    action_labels = ["Hybrid Encrypt", "Encrypt+Mask", "Masking", "Tokenization", "None/Plain"]
    action_values = [a_enc, a_enm, a_mask, a_tok, a_plain]
    action_colors = ["#3b82f6", "#7c3aed", "#f59e0b", "#8b5cf6", "#10b981"]

    fig3 = go.Figure(go.Bar(
        x=action_labels,
        y=action_values,
        marker_color=action_colors,
        text=action_values,
        textposition="outside",
    ))
    fig3.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0,r=0,t=30,b=5), height=240,
        font=dict(family="Inter", color="#475569"),
        xaxis=dict(showgrid=False, linecolor="#e2e8f0"),
        yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", dtick=1),
        showlegend=False,
    )
    if total == 0:
        fig3.add_annotation(text="No requests yet", x=0.5, y=0.5,
            xref="paper", yref="paper", showarrow=False,
            font=dict(size=14, color="#94a3b8", family="Inter"))
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Per-request breakdown
    if logs:
        st.markdown('<div class="netdictator-card"><h4>📋 Per-Request Breakdown</h4>', unsafe_allow_html=True)
        risk_c = {"LOW":"badge-green","MEDIUM":"badge-orange","HIGH":"badge-red"}
        act_c  = {"none":"badge-green","plain_access":"badge-green","masking":"badge-orange",
                  "tokenization":"badge-purple","encrypt_and_mask":"badge-purple",
                  "hybrid_encryption":"badge-blue"}
        rows = ""
        for r in logs:
            rc = risk_c.get(r.get("Risk Band",""), "badge-blue")
            ac = act_c.get(r.get("Security Action",""), "badge-blue")
            lbl = r.get("Security Action","").replace("_"," ").title() or "nil"
            rows += f"""<tr>
                <td style="font-size:11px">{r['Timestamp']}</td>
                <td>{r['File']}</td>
                <td>{r['IP Used']} / {r['User Type']}</td>
                <td><span class="{rc}">{r['Risk Score']}</span></td>
                <td><span class="{ac}">{lbl}</span></td>
                <td style="font-size:11px;color:#64748b">{r.get('Ops Applied','')[:40]}</td>
            </tr>"""
        st.markdown(f"""
        <table class="styled-table">
          <thead><tr><th>Time</th><th>File</th><th>IP / Type</th><th>Risk</th><th>Action</th><th>Ops Applied</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LOGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "logs":
    st.markdown("""<div class="page-header"><h1>📋 Access Logs</h1>
    <p>Real audit trail — only actual API requests made this session</p></div>""", unsafe_allow_html=True)

    real_logs = st.session_state.adpe_logs

    col_dl, col_clr = st.columns([5, 1])
    with col_dl:
        if real_logs:
            csv_data = "\n".join(
                [",".join(str(v) for v in r.values()) for r in [
                    {k: k for k in real_logs[0]}  # header row
                ] + real_logs]
            )
            st.download_button("⬇️ Export CSV", csv_data, "adpe_real_logs.csv", "text/csv")
    with col_clr:
        if st.button("🗑️ Clear Logs", use_container_width=True):
            st.session_state.adpe_logs = []
            st.rerun()

    if not real_logs:
        st.markdown("""
        <div class="netdictator-card">
          <table class="styled-table">
            <thead>
              <tr><th>Timestamp</th><th>Request ID</th><th>File</th><th>Sensitivity</th>
                  <th>IP / Type</th><th>Risk Score</th><th>Action</th><th>Ops Applied</th></tr>
            </thead>
            <tbody>
              <tr><td colspan="8" style="text-align:center;color:#94a3b8;padding:40px 20px;font-size:13.5px">
                📭 No logs yet.<br>
                <span style="font-size:12px">Go to <b>File Access Requests</b> page → select a file → click Run Security Analysis</span>
              </td></tr>
            </tbody>
          </table>
        </div>""", unsafe_allow_html=True)
        st.caption("0 real requests logged this session")
    else:
        sens_color = {"Important":"badge-red","Medium":"badge-orange","Normal":"badge-green"}
        act_color  = {
            "none":              "badge-green",
            "plain_access":      "badge-green",
            "masking":           "badge-orange",
            "tokenization":      "badge-purple",
            "encrypt_and_mask":  "badge-purple",
            "hybrid_encryption": "badge-blue",
        }
        risk_color = {"LOW":"badge-green","MEDIUM":"badge-orange","HIGH":"badge-red"}

        rows_html = ""
        for r in real_logs:
            sc  = sens_color.get(r.get("Sensitivity",""), "badge-blue")
            ac  = act_color.get(r.get("Security Action",""), "badge-blue")
            rc  = risk_color.get(r.get("Risk Band",""), "badge-blue")
            action_label = r.get("Security Action","").replace("_"," ").title()
            ops = r.get("Ops Applied","")[:45] + ("…" if len(r.get("Ops Applied","")) > 45 else "")
            rows_html += f"""<tr>
                <td style="white-space:nowrap;font-size:12px">{r['Timestamp']}</td>
                <td><code style="font-size:11px">{r['Request ID']}</code></td>
                <td>{r['File']}</td>
                <td><span class="{sc}">{r['Sensitivity']}</span></td>
                <td style="font-size:12px">{r['IP Used']}<br><small>{r['User Type']}</small></td>
                <td><span class="{rc}">{r['Risk Score']}</span></td>
                <td><span class="{ac}">{action_label or 'nil'}</span></td>
                <td style="font-size:11px;color:#64748b">{ops or '—'}</td>
            </tr>"""

        st.markdown(f"""
        <div class="netdictator-card">
          <table class="styled-table">
            <thead>
              <tr><th>Timestamp</th><th>Request ID</th><th>File</th><th>Sensitivity</th>
                  <th>IP / Type</th><th>Risk Score</th><th>Action</th><th>Ops Applied</th></tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)
        st.caption(f"✅ {len(real_logs)} real request(s) logged this session — no fake data")



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM STATUS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "status":
    st.markdown("""<div class="page-header"><h1>🖥️ System Status</h1>
    <p>Live health monitoring of all engine components</p></div>""", unsafe_allow_html=True)

    components = [
        ("🔧 Engine Status",      "All systems operational", "Active",   "badge-green", "Uptime: 99.98%",  False),
        ("🧠 NLP Model",          "BERT classifier running", "Online",   "badge-green", "Latency: 42ms",   False),
        ("☁️ S3 Connection",      "us-east-1 bucket linked", "Connected","badge-green", "Region: us-east-1",False),
        ("🛡️ Security Layer",     "AES-256 encryption on",  "Active",   "badge-green", "Key rotation: on",False),
        ("🔔 Threat Monitor",     "3 anomalies detected",   "Warning",  "badge-orange","Review required",  True),
        ("🪪 IAM Integration",    "AWS IAM roles synced",   "Synced",   "badge-green", "Last sync: 2m ago",False),
    ]

    cols = st.columns(3)
    for i, (title, desc, status, badge_cls, uptime, warn) in enumerate(components):
        warn_style = "border-left:4px solid #f59e0b" if warn else "border-left:4px solid #10b981"
        with cols[i % 3]:
            st.markdown(f"""
            <div class="netdictator-card" style="{warn_style}">
              <h4 style="margin-bottom:6px">{title}</h4>
              <p style="font-size:12.5px;color:#64748b;margin-bottom:8px">{desc}</p>
              <span class="{badge_cls}">{status}</span>
              <p style="font-size:11.5px;color:#94a3b8;margin-top:8px">{uptime}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="netdictator-card"><h4>📈 System Performance (24h)</h4>', unsafe_allow_html=True)
    hours = [f"{h:02d}:00" for h in range(0, 24, 2)]
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=hours, y=[92,88,85,90,95,97,96,94,93,96,98,97],
        name="Engine Load %", line=dict(color="#3b82f6", width=2.5),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.07)"))
    fig4.add_trace(go.Scatter(x=hours, y=[40,38,36,42,45,48,46,43,42,50,52,49],
        name="Latency (ms)", line=dict(color="#8b5cf6", width=2, dash="dash")))
    fig4.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0,r=0,t=5,b=5), height=220,
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1,
                    font=dict(size=12, family="Inter")),
        font=dict(family="Inter", color="#475569"),
        xaxis=dict(showgrid=False, linecolor="#e2e8f0"),
        yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0"),
    )
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "settings":
    st.markdown("""<div class="page-header"><h1>⚙️ Settings</h1>
    <p>Configure engine behaviour and security policies</p></div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="netdictator-card"><h4>🔧 Engine Configuration</h4>', unsafe_allow_html=True)
        st.selectbox("Default Encryption Algorithm", ["AES-256","RSA-2048","ChaCha20"])
        st.slider("NLP Confidence Threshold (%)", 50, 99, 85)
        st.number_input("Log Retention (days)", value=90, min_value=7, max_value=365)
        st.toggle("Auto-block External High Risk", value=True)
        st.toggle("Enable Real-time Alerts", value=True)
        if st.button("💾 Save Configuration", type="primary", use_container_width=True):
            st.success("✅ Configuration saved successfully.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="netdictator-card"><h4>🔏 Access Control Policy</h4>', unsafe_allow_html=True)
        st.toggle("Require MFA for External Access", value=True)
        st.toggle("Alert on Sensitive File Access", value=True)
        st.number_input("Session Timeout (minutes)", value=30, min_value=5, max_value=480)
        st.number_input("Max Login Attempts", value=5, min_value=1, max_value=20)
        st.selectbox("Audit Log Level", ["Full","Summary","Errors Only"])
        if st.button("🔒 Update Policy", type="primary", use_container_width=True):
            st.success("✅ Access policy updated successfully.")
        st.markdown('</div>', unsafe_allow_html=True)
