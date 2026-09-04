from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode, JsCode

from stockscreener.pipeline import ScanCancelled, load_cached_scan, recent_scan_logs, run_scan
from stockscreener.providers import enrich_company_profiles

st.set_page_config(page_title="Quality Dip Scanner", page_icon="Q", layout="wide")

st.html(
    """
    <style>
    :root {
        --ink: #eef5f1;
        --muted: #9aa9a8;
        --line: #2d393b;
        --paper: #0f1416;
        --panel: #171e20;
        --coral: #ff7058;
        --teal: #55c2ae;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--paper);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1540px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #141b1d;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem;
    }

    [data-testid="stSidebarNav"] {
        display: none;
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: var(--ink) !important;
    }

    [data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        box-shadow: 0 5px 18px rgba(23, 33, 43, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    [data-testid="stMetricValue"] {
        color: var(--ink);
        font-size: 1.7rem;
        font-weight: 750;
    }

    [data-testid="stExpander"] {
        border-color: var(--line);
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.65);
    }

    .brandbar {
        align-items: center;
        display: flex;
        justify-content: space-between;
        margin-bottom: 2.2rem;
    }

    [data-testid="stSidebar"] .brandbar {
        margin-bottom: 1.25rem;
        margin-top: -5.5rem;
        padding-top: 0.5rem;
        pointer-events: none;
    }

    [data-testid="stSidebar"] [data-testid="stHtml"] {
        pointer-events: none;
    }

    .sidebar-nav-label {
        color: var(--muted);
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        margin: 0.6rem 0 0.35rem;
        text-transform: uppercase;
    }

    .sidebar-nav-divider {
        border-top: 1px solid var(--line);
        margin: 0.75rem 0 1.15rem;
    }

    [data-testid="stSidebar"] a[data-testid="stPageLink"] {
        border-radius: 8px;
        padding: 0.45rem 0.55rem;
    }

    [data-testid="stSidebar"] a[data-testid="stPageLink"]:hover {
        background: #202a2c;
    }

    .brand {
        align-items: center;
        display: flex;
        gap: 0.7rem;
    }

    .brand-mark {
        align-items: center;
        background: var(--coral);
        border-radius: 9px;
        color: #ffffff;
        display: flex;
        font-size: 0.75rem;
        font-weight: 800;
        height: 30px;
        justify-content: center;
        letter-spacing: 0.04em;
        width: 30px;
    }

    .brand-name {
        color: var(--ink);
        font-size: 0.92rem;
        font-weight: 800;
        letter-spacing: -0.01em;
    }

    .brand-context {
        color: var(--muted);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        margin-top: 0.12rem;
        text-transform: uppercase;
    }

    .status-pill {
        background: #173b36;
        border: 1px solid #28675d;
        border-radius: 999px;
        color: var(--teal);
        font-size: 0.7rem;
        font-weight: 750;
        padding: 0.38rem 0.7rem;
    }

    .section-kicker {
        color: var(--coral);
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
    }

    .section-title {
        color: var(--ink);
        font-size: 1.65rem;
        font-weight: 780;
        letter-spacing: -0.035em;
        margin-bottom: 0.35rem;
    }

    .section-copy {
        color: var(--muted);
        font-size: 0.9rem;
        margin-bottom: 1.25rem;
    }

    [data-testid="stMarkdownContainer"] p {
        color: var(--ink);
    }

    .stButton > button[kind="primary"] {
        background: var(--coral);
        border-color: var(--coral);
        color: #ffffff;
        box-shadow: 0 5px 12px rgba(240, 100, 73, 0.22);
    }

    .stButton > button[kind="primary"]:hover {
        background: #d9553d;
        border-color: #d9553d;
    }
    </style>
    """
)


@st.cache_resource
def get_scan_executor() -> ThreadPoolExecutor:
    return ThreadPoolExecutor(max_workers=1)


SCAN_EXECUTOR = get_scan_executor()


def start_scan(period: str) -> None:
    cancel_event = Event()
    st.session_state.scan_event = cancel_event
    st.session_state.scan_period = period
    st.session_state.scan_future = SCAN_EXECUTOR.submit(run_scan, period=period, cancel_event=cancel_event)
    st.session_state.scan_running = True


def cancel_scan() -> None:
    event = st.session_state.get("scan_event")
    if event is not None:
        event.set()


@st.fragment(run_every=1)
def render_scan_progress() -> bool:
    future = st.session_state.get("scan_future")
    if future is None:
        return False
    if not future.done():
        st.info("Scan läuft ...")
        st.button("Scan abbrechen", on_click=cancel_scan, width="stretch")
        return True
    try:
        st.session_state.result = future.result()
        st.session_state.result_period = st.session_state.get("scan_period")
        st.session_state.scan_error = None
    except ScanCancelled as exc:
        st.session_state.result = None
        st.session_state.scan_error = str(exc)
    except Exception as exc:
        st.session_state.result = None
        st.session_state.scan_error = str(exc)
    finally:
        st.session_state.scan_future = None
        st.session_state.scan_event = None
        st.session_state.scan_running = False
    st.rerun(scope="app")


if "scan_running" not in st.session_state:
    st.session_state.scan_running = False
if "result" not in st.session_state:
    st.session_state.result = None


with st.sidebar:
    st.html(
        """
        <div class="brandbar">
            <div class="brand">
                <div class="brand-mark">QD</div>
                <div>
                    <div class="brand-name">Quality Dip Scanner</div>
                    <div class="brand-context">Nasdaq-100 signal desk</div>
                </div>
            </div>
        </div>
        """
    )
    st.markdown('<div class="sidebar-nav-label">Workspace</div>', unsafe_allow_html=True)
    st.page_link("app.py", label="Scanner", icon=":material/dashboard:")
    st.page_link(
        "pages/Bewertungslogik.py",
        label="Bewertungslogik",
        icon=":material/rule:",
    )
    st.markdown('<div class="sidebar-nav-divider"></div>', unsafe_allow_html=True)
    min_overall = st.slider("Mindestscore", 0, 100, 40)
    lookback = st.selectbox("Kurs-Historie", ["1y", "2y", "5y"], index=2)
    scan_running = st.session_state.get("scan_future") is not None
    run = st.button(
        "Scan aktualisieren",
        type="primary",
        width="stretch",
        icon=":material/refresh:",
        disabled=scan_running,
        on_click=start_scan,
        args=(lookback,),
    )

if st.session_state.get("scan_future") is None and st.session_state.get("result_period") != lookback:
    st.session_state.result = load_cached_scan(lookback)
    st.session_state.result_period = lookback
    st.session_state.scan_error = None

if render_scan_progress():
    st.stop()

result = st.session_state.result
if result is not None and "business_model" not in result.columns:
    result = enrich_company_profiles(result)
    st.session_state.result = result
if result is None:
    if st.session_state.get("scan_error"):
        st.error(f"Scan fehlgeschlagen: {st.session_state.scan_error}")
    else:
        st.info("Noch kein Scan gestartet. Klicke auf 'Scan aktualisieren'.")
    with st.expander("Scan-Protokoll"):
        st.dataframe(recent_scan_logs(), width="stretch", hide_index=True)
    st.stop()
signals = result[result["overall_score"] >= min_overall].copy()

metric_cols = st.columns(4)
metric_cols[0].metric("Universum", f"{len(result)} Titel", border=True)
metric_cols[1].metric("Kandidaten", f"{len(signals)}", border=True)
metric_cols[2].metric("Top quality", f"{result.quality_score.max():.0f}", border=True)
metric_cols[3].metric("Top overall", f"{result.overall_score.max():.0f}", border=True)

st.markdown(
    """
    <div class="section-kicker">Signal board</div>
    <div class="section-title">Quality-dip ranking</div>
    <div class="section-copy">Unternehmen mit ungewöhnlichem Rückgang, solider Qualität und attraktiver Bewertung.</div>
    """,
    unsafe_allow_html=True,
)
columns = {
    "ticker": "Ticker", "company_name": "Unternehmen", "sector": "Sektor",
    "sector_trend": "Sektortrend", "sector_trend_6m": "Sektortrend 6M",
    "business_model": "Geschäftsmodell",
    "price_change_5d": "5T", "drawdown_52w": "52W DD", "dip_score": "Dip",
    "quality_score": "Quality", "valuation_score": "Value", "overall_score": "Overall",
}
ranking = signals[list(columns)].rename(columns=columns)
grid_builder = GridOptionsBuilder.from_dataframe(ranking)
grid_builder.configure_default_column(
    filter=True, sortable=True, resizable=True, floatingFilter=True
)
percent_formatter = JsCode(
    """function(params) {
        return params.value == null ? '' : (params.value * 100).toFixed(1) + '%';
    }"""
)
score_formatter = JsCode(
    """function(params) {
        return params.value == null ? '' : Number(params.value).toFixed(0);
    }"""
)
for column in ["5T", "52W DD"]:
    grid_builder.configure_column(column, valueFormatter=percent_formatter)
for column in ["Dip", "Quality", "Value", "Overall"]:
    grid_builder.configure_column(column, valueFormatter=score_formatter)
grid_builder.configure_selection(selection_mode="single", use_checkbox=False)
grid_builder.configure_grid_options(domLayout="normal")
grid = AgGrid(
    ranking,
    gridOptions=grid_builder.build(),
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    fit_columns_on_grid_load=False,
    height=500,
    theme="streamlit",
    allow_unsafe_jscode=True,
    key="quality_dip_ranking",
)

if not signals.empty:
    selected_rows = grid.get("selected_rows")
    if hasattr(selected_rows, "to_dict"):
        selected_rows = selected_rows.to_dict("records")
    selected_rows = selected_rows or []
    if selected_rows:
        st.session_state.selected_ticker = selected_rows[0]["Ticker"]
    if st.session_state.get("selected_ticker") not in signals.ticker.tolist():
        st.session_state.selected_ticker = signals.iloc[0].ticker
    selected = st.session_state.selected_ticker
    row = signals.loc[signals.ticker == selected].iloc[0]
    left, right = st.columns([1, 1], gap="large")
    with left:
        with st.container(border=True):
            st.caption("Selected company")
            st.subheader(f"{row.company_name} ({row.ticker})")
            st.link_button(
                "Yahoo Finanzen Profi-Chart",
                f"https://de.finance.yahoo.com/quote/{row.ticker}/",
                icon=":material/open_in_new:",
                width="stretch",
            )
            st.write(f"**Geschäftsmodell:** {row.business_model}")
            st.write(row.business_description)
            st.write(row.reason)
            st.metric("Sektortrend", row.sector_trend, border=True)
            st.metric("Sektortrend 6M", row.sector_trend_6m, border=True)
            st.metric("5 Tage", f"{row.price_change_5d:.1%}", delta=f"relativ {row.relative_return_5d:.1%}", border=True)
            st.metric("52-Wochen-Drawdown", f"{row.drawdown_52w:.1%}", border=True)
    with right:
        with st.container(border=True):
            st.caption("Signal composition")
            st.subheader("Score-Aufteilung")
            st.bar_chart(row[["dip_score", "quality_score", "valuation_score"]])
else:
    st.info("Keine Titel erreichen den gewählten Mindestscore.")

st.caption(f"Quelle: yfinance + SEC | Stand: {result.as_of.max().date()}")

with st.expander("Scan-Protokoll"):
    st.dataframe(recent_scan_logs(), width="stretch", hide_index=True)
