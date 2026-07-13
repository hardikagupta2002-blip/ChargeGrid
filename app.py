import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
from data_engine import ChargeGridDataEngine

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ChargeGrid Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
  }

  .stApp {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1a2e 50%, #071320 100%);
    color: #e2e8f0;
  }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1a2e 0%, #091525 100%);
    border-right: 1px solid #1e3a5f;
  }
  section[data-testid="stSidebar"] * {
    color: #c8d8ec !important;
    font-size: 0.97rem !important;
  }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stSlider label,
  section[data-testid="stSidebar"] .stRadio label,
  section[data-testid="stSidebar"] .stMultiSelect label {
    color: #7ec8f7 !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  /* Radio nav items */
  section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    color: #dde8f5 !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    padding: 4px 0;
  }
  /* Sidebar brand text */
  .sidebar-brand-title { font-size: 1.5rem !important; font-weight: 700; color: #00d4ff; letter-spacing: 0.05em; }
  .sidebar-brand-sub   { font-size: 0.82rem !important; color: #8aacd4; text-transform: uppercase; letter-spacing: 0.12em; }

  /* ── KPI cards ── */
  .kpi-card {
    background: linear-gradient(135deg, #0d1f3c 0%, #112944 100%);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(0,150,255,0.15); }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #00d4ff, #0096ff);
    border-radius: 16px 16px 0 0;
  }
  .kpi-card.green::before  { background: linear-gradient(90deg, #00e676, #00bfa5); }
  .kpi-card.amber::before  { background: linear-gradient(90deg, #ffab00, #ff6d00); }
  .kpi-card.red::before    { background: linear-gradient(90deg, #ff1744, #d500f9); }
  .kpi-card.purple::before { background: linear-gradient(90deg, #7c4dff, #00b0ff); }

  .kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
    margin-bottom: 6px;
  }
  .kpi-label {
    font-size: 0.72rem;
    color: #9fb3cc;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 600;
    margin-bottom: 4px;
  }
  .kpi-delta { font-size: 0.82rem; font-weight: 500; }
  .kpi-delta.pos { color: #00e676; }
  .kpi-delta.neg { color: #ff4f4f; }
  .kpi-delta.neu { color: #9fb3cc; }

  /* ── Section headers ── */
  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1e3a5f;
  }
  .section-header h2 {
    font-size: 1rem;
    font-weight: 600;
    color: #c3d4e8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0;
  }
  .section-dot { width: 8px; height: 8px; background: #00d4ff; border-radius: 50%; box-shadow: 0 0 8px #00d4ff; }

  /* ── Alert boxes ── */
  .alert-box {
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0;
    border-left: 4px solid;
    font-size: 0.88rem;
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }
  .alert-box.critical { background: rgba(255,23,68,0.16);  border-color: #ff1744; color: #ffb3ab; }
  .alert-box.warning  { background: rgba(255,171,0,0.16);  border-color: #ffab00; color: #ffe082; }
  .alert-box.ok       { background: rgba(0,230,118,0.16);  border-color: #00e676; color: #9dfcc4; }

  /* ── Status badges ── */
  .status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
  .badge-online  { background: rgba(0,230,118,0.22);  color: #4dffa6; border: 1px solid rgba(0,230,118,0.5); }
  .badge-offline { background: rgba(255,23,68,0.22);  color: #ff7a70; border: 1px solid rgba(255,23,68,0.5); }
  .badge-busy    { background: rgba(255,171,0,0.22);  color: #ffc94d; border: 1px solid rgba(255,171,0,0.5); }
  .badge-error   { background: rgba(213,0,249,0.22);  color: #f0a6ff; border: 1px solid rgba(213,0,249,0.5); }

  /* ── Live pulse ── */
  @keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.5; transform:scale(1.3); } }
  .live-dot  { display:inline-block; width:8px; height:8px; background:#00e676; border-radius:50%; margin-right:6px; animation:pulse 1.5s infinite; }
  .live-label { font-size:0.75rem; color:#00e676; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; }

  .stButton > button {
    background: linear-gradient(135deg, #0096ff, #00d4ff);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 0.5rem 1.4rem;
    font-family: 'Space Grotesk', sans-serif;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #0080e6, #00bcd4);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0,150,255,0.3);
  }

  /* ── Visibility / contrast upgrades ── */
  .stApp, .stApp p, .stApp li, .stApp span, .stApp label {
    font-size: 1rem;
  }
  .stMarkdown p { color: #dbe6f3; line-height: 1.55; }
  h1, h2, h3 { color: #f2f6fb !important; }
  .stCaption, [data-testid="stCaptionContainer"] { color: #a9bdd6 !important; font-size: 0.85rem !important; }

  /* Bump KPI card readability */
  .kpi-value { font-size: 2.6rem; }
  .kpi-label { font-size: 0.78rem; color: #b7c8e0; }

  /* Selectboxes / multiselect / inputs -- ensure text is bright on dark bg */
  .stSelectbox div[data-baseweb="select"] > div,
  .stMultiSelect div[data-baseweb="select"] > div {
    background-color: #0d1f3c !important;
    border-color: #2a4a72 !important;
    color: #f2f6fb !important;
  }
  div[data-baseweb="tag"] { background-color: #0096ff !important; }
  div[data-baseweb="tag"] span { color: #fff !important; font-weight: 600 !important; }

  /* Radio nav items: stronger contrast + clearer selected state */
  section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    color: #eef4fb !important;
  }

  /* ── Dataframes / tables: force a legible dark theme ── */
  [data-testid="stDataFrame"] {
    background-color: #0d1a2e !important;
    border: 1px solid #2a4a72 !important;
    border-radius: 10px;
  }
  [data-testid="stDataFrame"] * {
    color: #eaf1fa !important;
  }
  [data-testid="stDataFrame"] table {
    background-color: #0d1a2e !important;
  }
  [data-testid="stDataFrame"] thead tr th {
    background-color: #132a4a !important;
    color: #7ec8f7 !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em;
    border-bottom: 2px solid #2a4a72 !important;
  }
  [data-testid="stDataFrame"] tbody tr:nth-child(odd) {
    background-color: #0f2038 !important;
  }
  [data-testid="stDataFrame"] tbody tr:nth-child(even) {
    background-color: #0a1830 !important;
  }
  [data-testid="stDataFrame"] tbody tr:hover {
    background-color: #163258 !important;
  }

  /* Expander header contrast */
  [data-testid="stExpander"] summary {
    color: #eef4fb !important;
    font-weight: 600 !important;
  }
  [data-testid="stExpander"] {
    background-color: #0d1f3c !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
  }

  /* Divider color -- a bit brighter so sections read clearly */
  hr { border-color: #2a4a72 !important; opacity: 0.6; }

  /* Alert box text a touch larger and bolder for readability */
  .alert-box { font-size: 0.94rem; font-weight: 500; }
  .alert-box b { color: #ffffff; font-weight: 700; }
  .alert-box .alert-msg { color: inherit; opacity: 1 !important; font-size: 0.86rem !important; }
  .alert-box .alert-time { color: #cdd9ea !important; opacity: 1 !important; font-size: 0.75rem !important; font-weight: 600; }
  .alert-box .alert-meta { color: #cdd9ea !important; opacity: 1 !important; font-size: 0.72rem !important; font-weight: 600; text-transform: uppercase; }

  /* Info / warning banners from st.info() */
  [data-testid="stAlert"] { background-color: #0d1f3c !important; border: 1px solid #2a4a72 !important; }
  [data-testid="stAlert"] p { color: #eaf1fa !important; }

  /* ── Kill Streamlit's "stale/rerunning" fade-out overlay ──
     While the app auto-refreshes (st.rerun()), Streamlit dims the
     previous frame to ~50% opacity until the new one is ready. On a
     dark theme this looks like faded/ghosted "leftover" content from
     the last page. Force full opacity so nothing looks washed out. */
  [data-stale="true"], .main[data-stale="true"], .stApp [data-stale="true"] {
    opacity: 1 !important;
    transition: none !important;
  }
  div[data-testid="stAppViewContainer"] { opacity: 1 !important; }
</style>
""", unsafe_allow_html=True)

# ── Chart defaults ─────────────────────────────────────────────────────────────
# NOTE: Plotly does NOT accept the CSS keyword "transparent" for color
# properties like gridcolor / linecolor / outlinecolor. Use the rgba
# equivalent "rgba(0,0,0,0)" instead. This is what was causing the
# "ValueError: Invalid value of type 'builtins.str' ... " crash.
TRANSPARENT = "rgba(0,0,0,0)"

CHART_LAYOUT = dict(
    paper_bgcolor=TRANSPARENT,
    plot_bgcolor="rgba(13,26,60,0.4)",
    font=dict(family="Space Grotesk", color="#c3d4e8", size=13),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor="#2a4a72", linecolor="#2a4a72", tickfont=dict(size=12, color="#c3d4e8")),
    yaxis=dict(gridcolor="#2a4a72", linecolor="#2a4a72", tickfont=dict(size=12, color="#c3d4e8")),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#132a4a", font=dict(color="#eaf1fa", size=13), bordercolor="#2a4a72"),
    legend=dict(font=dict(color="#c3d4e8")),
)

def chart_layout(**overrides):
    """
    Safely build a layout dict from CHART_LAYOUT plus overrides.
    FIX: calling fig.update_layout(**CHART_LAYOUT, yaxis=dict(...)) crashes
    with "got multiple values for keyword argument 'yaxis'" because
    CHART_LAYOUT already defines 'xaxis'/'yaxis'. This helper merges those
    nested dicts instead of colliding on the keyword.
    """
    result = dict(CHART_LAYOUT)
    for key in ("xaxis", "yaxis", "legend"):
        if key in overrides:
            result[key] = {**result.get(key, {}), **overrides.pop(key)}
    result.update(overrides)
    return result

# ── UI helpers ─────────────────────────────────────────────────────────────────
def kpi(value, label, delta=None, color="blue"):
    delta_html = ""
    if delta is not None:
        sign = "+" if delta >= 0 else ""
        cls  = "pos" if delta > 0 else ("neg" if delta < 0 else "neu")
        symbol = "▲" if delta > 0 else ("▼" if delta < 0 else "●")
        delta_html = f'<div class="kpi-delta {cls}">{symbol} {sign}{delta:.1f}% vs yesterday</div>'
    return f"""
    <div class="kpi-card {color}">
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{label}</div>
      {delta_html}
    </div>"""

@st.cache_data(ttl=3600)
def get_upcoming_stations(cities):
    """
    Sample/placeholder data for planned charging stations that are not
    live yet. This is generated locally in app.py (not from data_engine.py)
    since the engine currently only models operational stations.
    Swap this out for a real data source (DB / API / CSV) when available.
    """
    rng = np.random.default_rng(42)
    names = ["Metro Plaza Hub", "Highway Junction Station", "Tech Park Charging Bay",
              "Riverside Fast-Charge Point", "Central Mall Supercharger", "Airport Connector Hub",
              "Innovation District EV Point", "Greenfield Transit Station"]
    port_types = ["Level 2", "DC Fast", "Supercharger"]
    statuses = ["Under Construction", "Permitting", "Site Survey", "Equipment Ordered"]

    rows = []
    n = min(len(cities), 8) if cities else 0
    chosen_cities = list(cities)[:n] if n else []
    for i, city in enumerate(chosen_cities):
        launch_offset = int(rng.integers(15, 180))
        rows.append({
            "Station Name": names[i % len(names)],
            "City": city,
            "Planned Port Type": port_types[int(rng.integers(0, len(port_types)))],
            "Planned Ports": int(rng.integers(4, 20)),
            "Status": statuses[int(rng.integers(0, len(statuses)))],
            "Est. Launch Date": (datetime.now() + timedelta(days=launch_offset)).strftime("%d %b %Y"),
            "Progress %": int(rng.integers(10, 95)),
        })
    return pd.DataFrame(rows)


def section(title):
    st.markdown(f"""
    <div class="section-header">
      <div class="section-dot"></div>
      <h2>{title}</h2>
    </div>""", unsafe_allow_html=True)

# ── Engine + session state ─────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return ChargeGridDataEngine()

engine = get_engine()

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True
if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 30

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 24px;">
      <div class="sidebar-brand-title">ChargeGrid</div>
      <div class="sidebar-brand-sub">Fleet Analytics Platform</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    page = st.radio("Navigation", [
        "Dashboard",
        "Live Sessions",
        "Station Map",
        "Port Health",
        "Trends and Forecasts",
        "Reports",
    ], label_visibility="collapsed")

    st.divider()

    st.markdown(
        '<p style="font-size:0.85rem; font-weight:700; text-transform:uppercase; '
        'letter-spacing:0.1em; color:#7ec8f7; margin-bottom:8px;">Filters</p>',
        unsafe_allow_html=True,
    )

    all_cities = engine.cities
    india_cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata"]
    us_cities    = [c for c in all_cities if c not in india_cities]

    region_filter = st.selectbox(
        "Region",
        ["All Regions", "India Only", "USA Only"],
        help="Quickly narrow to a region",
    )

    if region_filter == "India Only":
        default_cities = india_cities
    elif region_filter == "USA Only":
        default_cities = us_cities
    else:
        default_cities = all_cities

    city_filter = st.multiselect(
        "Cities",
        options=all_cities,
        default=default_cities,
        help="Select one or more cities",
    )

    port_type_filter = st.multiselect(
        "Port Type",
        options=["Level 2", "DC Fast", "Supercharger"],
        default=["Level 2", "DC Fast", "Supercharger"],
    )

    date_range = st.selectbox(
        "Date Range",
        options=[1, 3, 7, 14, 30],
        index=2,
        format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}",
    )

    st.divider()

    st.markdown(
        '<p style="font-size:0.85rem; font-weight:700; text-transform:uppercase; '
        'letter-spacing:0.1em; color:#7ec8f7; margin-bottom:8px;">Live Feed</p>',
        unsafe_allow_html=True,
    )

    auto_refresh = st.toggle("Auto Refresh", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh

    if auto_refresh:
        st.session_state.refresh_interval = st.select_slider(
            "Refresh every", options=[10, 15, 30, 60, 120],
            value=st.session_state.refresh_interval,
            format_func=lambda x: f"{x}s",
        )

    if st.button("Refresh Now", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.cache_data.clear()
        st.rerun()

    elapsed = (datetime.now() - st.session_state.last_refresh).seconds
    st.markdown(
        f'<p style="font-size:0.78rem; color:#7a9ac0; text-align:center; margin-top:8px;">Last updated {elapsed}s ago</p>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown(
        '<p style="font-size:0.75rem; color:#7a9ac0; text-align:center; line-height:1.5;">'
        'Data: Open-Meteo · Simulated EV Fleet<br>v2.1 · Real-Time Mode</p>',
        unsafe_allow_html=True,
    )

# ── Fallback if nothing selected ───────────────────────────────────────────────
if not city_filter:
    city_filter = engine.cities
if not port_type_filter:
    port_type_filter = ["Level 2", "DC Fast", "Supercharger"]

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_data(cities, port_types, days):
    return engine.get_all_data(cities, port_types, days)

data = load_data(tuple(city_filter), tuple(port_type_filter), date_range)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":

    col_title, col_live = st.columns([5, 1])
    with col_title:
        st.markdown("""
        <h1 style="font-size:2rem; font-weight:700; color:#fff; margin:0; letter-spacing:-0.02em;">
          City EV Charging Network <span style="color:#00d4ff;">Command Portal</span>
        </h1>
        <p style="color:#a9bdd6; font-size:0.88rem; margin-top:6px;">
          Real-time analytics across your entire charging fleet
        </p>""", unsafe_allow_html=True)
    with col_live:
        st.markdown(f"""
        <div style="text-align:right; padding-top:16px;">
          <span class="live-dot"></span>
          <span class="live-label">Live</span>
          <div style="font-size:0.68rem; color:#a9bdd6; margin-top:4px;">{datetime.now().strftime('%H:%M:%S')}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # Active filters summary
    with st.expander("Active Filters", expanded=True):
        fa, fb, fc = st.columns(3)
        with fa:
            st.markdown(f"**Region:** {region_filter}")
            st.markdown(f"**Cities selected:** {len(city_filter)}")
        with fb:
            st.markdown(f"**Port types:** {', '.join(port_type_filter)}")
        with fc:
            st.markdown(f"**Date range:** Last {date_range} day{'s' if date_range > 1 else ''}")

    st.divider()

    # KPI row
    kpis = data["kpis"]
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.markdown(kpi(f"{kpis['total_kw']:,.0f}", "kWh Delivered Today", kpis.get("kw_delta"), "blue"), unsafe_allow_html=True)
    with k2: st.markdown(kpi(str(kpis["active_sessions"]), "Active Sessions", color="green"), unsafe_allow_html=True)
    with k3: st.markdown(kpi(str(kpis["total_ports"]), "Total Ports Online", kpis.get("port_delta"), "purple"), unsafe_allow_html=True)
    with k4: st.markdown(kpi(str(kpis["error_ports"]), "Flagged / Error Ports", color="red"), unsafe_allow_html=True)
    with k5: st.markdown(kpi(f"${kpis['revenue']:,.0f}", "Revenue (Today)", kpis.get("rev_delta"), "amber"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Peak hours + donut
    section("Today's Grid Overview")
    col_a, col_b = st.columns([3, 2])

    with col_a:
        hours_df = data["hourly_kw"]
        fig_hours = go.Figure(go.Bar(
            x=hours_df["hour"], y=hours_df["kw"],
            marker=dict(color=hours_df["kw"], colorscale=[[0,"#0d3b6e"],[0.5,"#0096ff"],[1,"#00d4ff"]], showscale=False),
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} kWh<extra></extra>",
        ))
        fig_hours.update_layout(**chart_layout(title=dict(text="Peak Usage Hours (kWh)", font=dict(color="#c3d4e8", size=13)), height=300))
        st.plotly_chart(fig_hours, use_container_width=True)

    with col_b:
        status_counts = data["port_status_counts"]
        fig_donut = go.Figure(go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.65,
            marker=dict(colors=["#00e676","#ffab00","#ff1744","#7c4dff"]),
            hovertemplate="<b>%{label}</b><br>%{value} ports (%{percent})<extra></extra>",
            textinfo="none",
        ))
        fig_donut.update_layout(**chart_layout(
            title=dict(text="Port Status Distribution", font=dict(color="#c3d4e8", size=13)),
            height=300,
            showlegend=True,
            legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
            annotations=[dict(
                text=f"<b>{kpis['total_ports']}</b><br><span style='font-size:10px'>Ports</span>",
                x=0.5, y=0.5, font=dict(color="#fff", size=16), showarrow=False,
            )],
        ))
        st.plotly_chart(fig_donut, use_container_width=True)

    # kWh trend + city breakdown
    col_c, col_d = st.columns([3, 2])

    with col_c:
        section(f"{date_range}-Day kWh Delivery Trend")
        trend_df = data["daily_trend"]
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_df["date"], y=trend_df["kw"],
            mode="lines", fill="tozeroy",
            fillcolor="rgba(0,150,255,0.08)",
            line=dict(color="#00d4ff", width=2.5),
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} kWh<extra></extra>",
            name="kWh",
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend_df["date"], y=trend_df["sessions"],
            mode="lines", line=dict(color="#00e676", width=1.5, dash="dot"),
            yaxis="y2", name="Sessions",
            hovertemplate="<b>%{x}</b><br>%{y} sessions<extra></extra>",
        ))
        fig_trend.update_layout(**chart_layout(
            height=280,
            # FIX: use rgba(0,0,0,0) instead of the invalid "transparent" string
            yaxis2=dict(overlaying="y", side="right", gridcolor=TRANSPARENT, linecolor=TRANSPARENT, tickfont=dict(size=10, color="#00e676")),
            legend=dict(orientation="h", y=1.1, font=dict(size=10)),
        ))
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_d:
        section("kWh by City")
        city_df = data["city_kw"]
        fig_city = go.Figure(go.Bar(
            x=city_df["kw"], y=city_df["city"], orientation="h",
            marker=dict(color=city_df["kw"], colorscale=[[0,"#0d3b6e"],[1,"#00d4ff"]]),
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} kWh<extra></extra>",
        ))
        fig_city.update_layout(**chart_layout(height=280, yaxis=dict(autorange="reversed")))
        st.plotly_chart(fig_city, use_container_width=True)

    # Alerts
    section("Active Alerts")
    alerts = data["alerts"]
    if alerts:
        for a in alerts[:6]:
            lvl = a["level"]
            marker = "[!!]" if lvl == "critical" else "[!]"
            st.markdown(f"""
            <div class="alert-box {lvl}">
              <div>
                <b>{marker} {a['title']}</b><br>
                <span class="alert-msg">{a['message']}</span>
              </div>
              <span class="alert-time" style="margin-left:auto; white-space:nowrap;">{a['time']}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box ok"><b>All systems nominal</b> -- No active alerts at this time.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LIVE SESSIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Live Sessions":
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:700; color:#fff; margin:0;">
      Live <span style="color:#00e676;">Charging Sessions</span>
    </h1>
    <p style="color:#a9bdd6; font-size:0.88rem;">Real-time feed of all active and recent sessions</p>
    """, unsafe_allow_html=True)
    st.divider()

    sessions_df = data["live_sessions"]

    status_options = sorted(sessions_df["status"].unique().tolist())
    selected_statuses = st.multiselect("Filter by status", status_options, default=status_options)
    sessions_df = sessions_df[sessions_df["status"].isin(selected_statuses)]

    active = sessions_df[sessions_df["status"] == "Active"]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi(str(len(active)), "Currently Charging", color="green"), unsafe_allow_html=True)
    with c2: st.markdown(kpi(f"{active['kw_now'].sum():.1f}", "kW Drawing Right Now", color="blue"), unsafe_allow_html=True)
    with c3:
        avg_min = active["duration_min"].mean() if len(active) else 0
        st.markdown(kpi(f"{avg_min:.0f}", "Avg Session Min", color="purple"), unsafe_allow_html=True)
    with c4: st.markdown(kpi(str(len(sessions_df[sessions_df["status"] == "Error"])), "Error Sessions", color="red"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section("Live Session Feed")

    def color_status(val):
        colors = {
            "Active":    "background-color: rgba(0,230,118,0.1); color: #00e676",
            "Completed": "background-color: rgba(0,150,255,0.1); color: #64b5f6",
            "Error":     "background-color: rgba(255,23,68,0.1); color: #ff4f4f",
            "Aborted":   "background-color: rgba(255,171,0,0.1); color: #ffab00",
        }
        return colors.get(val, "")

    display_df = sessions_df.rename(columns={
        "session_id": "Session ID", "port_id": "Port ID", "city": "City",
        "port_type": "Type", "status": "Status", "kw_now": "kW Now",
        "kw_delivered": "kWh Total", "duration_min": "Duration (min)",
        "vehicle": "Vehicle", "started": "Started",
    })
    styled = display_df.style.map(color_status, subset=["Status"]).format({
        "kW Now": "{:.1f}", "kWh Total": "{:.1f}", "Duration (min)": "{:.0f}",
    })
    st.dataframe(styled, use_container_width=True, height=420)

    section("Live Grid Power Draw")
    current_draw = float(active["kw_now"].sum())
    max_capacity = 2500

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_draw,
        delta={"reference": max_capacity * 0.6},
        title={"text": "Current Grid Load (kW)", "font": {"color": "#c3d4e8", "size": 14}},
        gauge={
            "axis": {"range": [0, max_capacity], "tickcolor": "#c3d4e8"},
            "bar": {"color": "#00d4ff"},
            "bgcolor": "#0d1a2e",
            "bordercolor": "#1e3a5f",
            "steps": [
                {"range": [0, 800],    "color": "rgba(0,230,118,0.15)"},
                {"range": [800, 1600], "color": "rgba(255,171,0,0.15)"},
                {"range": [1600,2500], "color": "rgba(255,23,68,0.15)"},
            ],
            "threshold": {"line": {"color": "#ff1744", "width": 3}, "value": 2000},
        },
        number={"suffix": " kW", "font": {"color": "#00d4ff", "size": 36}},
    ))
    fig_gauge.update_layout(paper_bgcolor=TRANSPARENT, font=dict(color="#c3d4e8"), height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: STATION MAP
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Station Map":
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:700; color:#fff; margin:0;">
      Station <span style="color:#00d4ff;">Network Map</span>
    </h1>
    <p style="color:#a9bdd6; font-size:0.88rem;">Geographic distribution of all charging stations</p>
    """, unsafe_allow_html=True)
    st.divider()

    stations_df = data["stations"]
    color_map = {"Online": "#00e676", "Offline": "#ff1744", "Busy": "#ffab00", "Error": "#ea80fc"}

    status_filter = st.multiselect(
        "Filter by station status",
        options=sorted(stations_df["status"].unique().tolist()),
        default=sorted(stations_df["status"].unique().tolist()),
    )
    stations_df = stations_df[stations_df["status"].isin(status_filter)]

    if len(stations_df) == 0:
        st.info("No stations match the selected filters.")
    else:
        centre_lat = stations_df["lat"].mean()
        centre_lon = stations_df["lon"].mean()

        fig_map = px.scatter_mapbox(
            stations_df,
            lat="lat", lon="lon",
            color="status",
            size="total_ports",
            hover_name="name",
            hover_data={"lat": False, "lon": False, "city": True, "port_type": True,
                        "total_ports": True, "active_sessions": True, "kw_today": ":.0f"},
            color_discrete_map=color_map,
            size_max=20,
            zoom=3,
            center={"lat": centre_lat, "lon": centre_lon},
            mapbox_style="carto-darkmatter",
        )
        fig_map.update_layout(
            paper_bgcolor=TRANSPARENT,
            margin=dict(l=0, r=0, t=0, b=0),
            height=520,
            legend=dict(bgcolor="rgba(13,26,60,0.8)", bordercolor="#1e3a5f", font=dict(color="#c3d4e8")),
        )
        st.plotly_chart(fig_map, use_container_width=True)

    section("Station Directory")
    st.dataframe(
        stations_df[["name","city","port_type","total_ports","active_sessions","kw_today","status"]]
        .rename(columns={"name":"Station","city":"City","port_type":"Type",
                         "total_ports":"Ports","active_sessions":"Active","kw_today":"kWh Today","status":"Status"}),
        use_container_width=True, height=350,
    )

    section("Upcoming Charging Stations")
    upcoming_df = get_upcoming_stations(city_filter)
    if upcoming_df.empty:
        st.info("No upcoming stations planned for the selected cities.")
    else:
        u1, u2, u3 = st.columns(3)
        with u1: st.markdown(kpi(str(len(upcoming_df)), "Stations In Pipeline", color="purple"), unsafe_allow_html=True)
        with u2: st.markdown(kpi(str(int(upcoming_df["Planned Ports"].sum())), "Planned Ports", color="blue"), unsafe_allow_html=True)
        with u3: st.markdown(kpi(f"{upcoming_df['Progress %'].mean():.0f}%", "Avg. Build Progress", color="amber"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        def progress_color(val):
            if val >= 70:
                return "color: #00e676; font-weight:600"
            elif val >= 40:
                return "color: #ffab00; font-weight:600"
            return "color: #ff8a80; font-weight:600"

        st.dataframe(
            upcoming_df.style.map(progress_color, subset=["Progress %"]).format({"Progress %": "{}%"}),
            use_container_width=True, height=300,
        )
        st.caption("Sample placeholder data -- replace get_upcoming_stations() with a real data source (database, CSV, or API) when available.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PORT HEALTH
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Port Health":
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:700; color:#fff; margin:0;">
      Port <span style="color:#ff4f4f;">Health Monitor</span>
    </h1>
    <p style="color:#a9bdd6; font-size:0.88rem;">Automated fault detection -- ports flagged for repeated errors</p>
    """, unsafe_allow_html=True)
    st.divider()

    health_df = data["port_health"]
    flagged = health_df[health_df["flagged"] == True]
    healthy = health_df[health_df["flagged"] == False]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(kpi(str(len(health_df)), "Total Ports Monitored", color="blue"), unsafe_allow_html=True)
    with c2: st.markdown(kpi(str(len(healthy)), "Healthy Ports", color="green"), unsafe_allow_html=True)
    with c3: st.markdown(kpi(str(len(flagged)), "Flagged for Review", color="red"), unsafe_allow_html=True)
    error_pct = len(flagged) / max(len(health_df), 1) * 100
    with c4: st.markdown(kpi(f"{error_pct:.1f}%", "Error Rate", color="amber"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section("Flagged Ports -- Requires Immediate Attention")

    if len(flagged) > 0:
        for _, row in flagged.iterrows():
            lvl = "critical" if row["error_count"] >= 5 else "warning"
            badge = "CRITICAL" if lvl == "critical" else "WARNING"
            st.markdown(f"""
            <div class="alert-box {lvl}" style="margin-bottom:8px;">
              <div style="min-width:60px; text-align:center;">
                <div class="alert-meta">{row['port_type']}</div>
              </div>
              <div style="flex:1">
                <b>Port {row['port_id']}</b> -- {row['station_name']}, {row['city']}
                <br><span class="alert-msg">
                  {row['error_count']} errors in last 7 days &middot; Last error: {row['last_error']} &middot;
                  Success rate: {row['success_rate']:.0f}%
                </span>
              </div>
              <div style="text-align:right; white-space:nowrap;">
                <span class="status-badge badge-error">{badge}</span>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box ok"><b>No flagged ports</b> -- All ports performing within acceptable thresholds.</div>', unsafe_allow_html=True)

    section("Error Rate by Port Type (Last 7 Days)")
    error_trend = data["error_trend"]
    if not error_trend.empty:
        fig_err = px.line(
            error_trend, x="date", y="errors", color="port_type",
            color_discrete_map={"Level 2": "#00d4ff", "DC Fast": "#ffab00", "Supercharger": "#7c4dff"},
            markers=True,
        )
        fig_err.update_layout(**chart_layout(height=280, legend=dict(orientation="h", y=1.1)))
        st.plotly_chart(fig_err, use_container_width=True)
    else:
        st.info("No error data for the selected filters.")

    section("Full Port Health Registry")
    def flag_color(val):
        return "color: #ff4f4f; font-weight:600" if val else "color: #00e676"
    st.dataframe(
        health_df.style.map(flag_color, subset=["flagged"]).format({"success_rate": "{:.0f}%", "avg_kw": "{:.1f}"}),
        use_container_width=True, height=380,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TRENDS & FORECASTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Trends and Forecasts":
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:700; color:#fff; margin:0;">
      Trends and <span style="color:#7c4dff;">Forecasts</span>
    </h1>
    <p style="color:#a9bdd6; font-size:0.88rem;">Historical patterns and 7-day demand forecast</p>
    """, unsafe_allow_html=True)
    st.divider()

    section("Usage Heatmap -- Hour of Day vs Day of Week")
    heatmap_df = data["heatmap"]
    fig_heat = go.Figure(go.Heatmap(
        z=heatmap_df.values,
        x=[f"{h:02d}:00" for h in heatmap_df.columns.tolist()],
        y=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        colorscale=[[0,"#071320"],[0.4,"#0d3b6e"],[0.7,"#0096ff"],[1,"#00d4ff"]],
        hovertemplate="<b>%{y}, %{x}</b><br>%{z:,.0f} kWh<extra></extra>",
        showscale=True,
        # FIX: outlinecolor must be a real color value, not the string "transparent"
        colorbar=dict(tickfont=dict(color="#c3d4e8"), outlinecolor=TRANSPARENT),
    ))
    fig_heat.update_layout(**chart_layout(height=280))
    st.plotly_chart(fig_heat, use_container_width=True)

    section("7-Day Demand Forecast")
    forecast_df = data["forecast"]
    fig_fc = go.Figure()
    hist = forecast_df[forecast_df["type"] == "historical"]
    fc   = forecast_df[forecast_df["type"] == "forecast"]

    fig_fc.add_trace(go.Scatter(x=hist["date"], y=hist["kw"], mode="lines", name="Historical", line=dict(color="#00d4ff", width=2)))
    fig_fc.add_trace(go.Scatter(x=fc["date"],   y=fc["kw"],   mode="lines", name="Forecast",   line=dict(color="#7c4dff", width=2, dash="dash")))
    fig_fc.add_trace(go.Scatter(
        x=fc["date"].tolist() + fc["date"].tolist()[::-1],
        y=fc["upper"].tolist() + fc["lower"].tolist()[::-1],
        fill="toself", fillcolor="rgba(124,77,255,0.1)",
        line=dict(color=TRANSPARENT), name="Confidence Band",
    ))
    fig_fc.update_layout(**chart_layout(height=320, legend=dict(orientation="h", y=1.1)))
    st.plotly_chart(fig_fc, use_container_width=True)

    col_x, col_y = st.columns(2)
    with col_x:
        section("Revenue by Port Type")
        rev_df = data["revenue_by_type"]
        fig_rev = go.Figure(go.Bar(
            x=rev_df["port_type"], y=rev_df["revenue"],
            marker=dict(color=["#00d4ff","#ffab00","#7c4dff"]),
            hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
        ))
        fig_rev.update_layout(**chart_layout(height=280))
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_y:
        section("Avg Session Duration by City")
        dur_df = data["duration_by_city"]
        fig_dur = go.Figure(go.Bar(
            x=dur_df["city"], y=dur_df["avg_duration"],
            marker=dict(color=dur_df["avg_duration"], colorscale=[[0,"#0d3b6e"],[1,"#00e676"]]),
            hovertemplate="<b>%{x}</b><br>%{y:.0f} min<extra></extra>",
        ))
        fig_dur.update_layout(**chart_layout(height=280))
        st.plotly_chart(fig_dur, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Reports":
    st.markdown("""
    <h1 style="font-size:1.8rem; font-weight:700; color:#fff; margin:0;">
      Reports and <span style="color:#00d4ff;">Export</span>
    </h1>
    <p style="color:#a9bdd6; font-size:0.88rem;">Download data for offline analysis</p>
    """, unsafe_allow_html=True)
    st.divider()

    section("Export Data")
    col1, col2, col3 = st.columns(3)
    with col1:
        csv_sessions = data["live_sessions"].to_csv(index=False).encode()
        st.download_button("Download Session Logs (.csv)", csv_sessions, "sessions.csv", "text/csv", use_container_width=True)
    with col2:
        csv_health = data["port_health"].to_csv(index=False).encode()
        st.download_button("Download Port Health Report (.csv)", csv_health, "port_health.csv", "text/csv", use_container_width=True)
    with col3:
        csv_stations = data["stations"].to_csv(index=False).encode()
        st.download_button("Download Station Directory (.csv)", csv_stations, "stations.csv", "text/csv", use_container_width=True)

    section("Summary Statistics")
    kpis = data["kpis"]
    summary = {
        "Metric": ["Total kWh Delivered Today", "Active Sessions", "Total Ports",
                   "Error Ports", "Revenue Today", "Fleet Uptime %"],
        "Value": [
            f"{kpis['total_kw']:,.0f} kWh",
            str(kpis["active_sessions"]),
            str(kpis["total_ports"]),
            str(kpis["error_ports"]),
            f"${kpis['revenue']:,.0f}",
            f"{(kpis['total_ports'] - kpis['error_ports']) / max(kpis['total_ports'],1) * 100:.1f}%",
        ],
    }
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

    section("Full Session Log")
    st.dataframe(data["live_sessions"], use_container_width=True, height=400)


# ── Auto-refresh ───────────────────────────────────────────────────────────────
if st.session_state.auto_refresh:
    time.sleep(st.session_state.refresh_interval)
    st.session_state.last_refresh = datetime.now()
    st.rerun()