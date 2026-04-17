# app/streamlit_app.py
# ──────────────────────────────────────────────────────────────────────
# AIRI Streamlit Application — Entry Point
# Run from project root: streamlit run app/streamlit_app.py
# ──────────────────────────────────────────────────────────────────────

import sys
from pathlib import Path

import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="AIRI — AI Readiness Index",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --airi-primary: #2563EB;
        --airi-primary-dark: #1D4ED8;
        --airi-primary-soft: #DBEAFE;
        --airi-text: #111827;
        --airi-subtle: #4B5563;
        --airi-border: #E5E7EB;
    }
    .stApp {
        background: #F5F7FB;
        color: var(--airi-text);
    }
    [data-testid="stSidebar"] {
        display: none;
    }
    .block-container {
        padding-top: 4.4rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .airi-top {
        background: #FFFFFF;
        border: 1px solid var(--airi-border);
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 8px;
    }
    .airi-top-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
    }
    .airi-title {
        margin: 0;
        color: var(--airi-text) !important;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .airi-subtitle {
        margin: 4px 0 0 0;
        color: var(--airi-subtle) !important;
        font-size: 0.95rem;
    }
    .airi-badge {
        display: inline-block;
        margin-top: 2px;
        background: #EFF6FF;
        color: var(--airi-primary-dark);
        border: 1px solid var(--airi-primary-soft);
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.78rem;
        font-weight: 600;
        white-space: nowrap;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stWidgetLabel"] p {
        font-size: 0;
        margin: 0;
    }
    div[role="radiogroup"][aria-label="Main Navigation"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 4px 10px;
        margin: 8px 0 18px 0;
    }
    div[role="radiogroup"][aria-label="Main Navigation"] label[data-baseweb="radio"] {
        padding: 6px 2px;
        margin-right: 10px;
    }
    div[role="radiogroup"][aria-label="Main Navigation"] label[data-baseweb="radio"] span {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
    }
    div[role="radiogroup"][aria-label="Main Navigation"] label[data-baseweb="radio"][aria-checked="true"] span {
        color: var(--airi-primary-dark) !important;
    }
    .stButton > button,
    .stDownloadButton > button {
        background: var(--airi-primary) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--airi-primary) !important;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: var(--airi-primary-dark) !important;
        border-color: var(--airi-primary-dark) !important;
        color: #FFFFFF !important;
    }
    .stProgress > div > div > div > div {
        background-color: var(--airi-primary) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="airi-top">
        <div class="airi-top-row">
            <div>
                <h1 class="airi-title">AI Readiness Index</h1>
                <p class="airi-subtitle">UK Debt Management Assessment Tool</p>
            </div>
            <span class="airi-badge">● Financial Services Edition</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

pages = {
    "Dashboard": "pages/1_Dashboard.py",
    "Assessment": "pages/1_Assessment.py",
    "Results": "pages/2_Results.py",
    "Recommendations": "pages/3_Recommendations.py",
}
page_icons = {
    "Dashboard": "📊",
    "Assessment": "📝",
    "Results": "📈",
    "Recommendations": "💡",
}

PAGE_KEYS = list(pages.keys())

# Initialise the radio widget state to Dashboard on first load.
if "main_nav_widget" not in st.session_state:
    st.session_state.main_nav_widget = "Dashboard"

# Pages request navigation by setting st.session_state.nav_goto = "PageName".
# We apply it here BEFORE the radio renders (setting a keyed widget value
# before render is allowed; setting it after raises an error).
if "nav_goto" in st.session_state:
    target = st.session_state.pop("nav_goto")
    if target in PAGE_KEYS:
        st.session_state.main_nav_widget = target

selection = st.radio(
    "Main Navigation",
    PAGE_KEYS,
    horizontal=True,
    key="main_nav_widget",
    format_func=lambda x: f"{page_icons[x]}  {x}",
    label_visibility="collapsed",
)

page_file = PROJECT_ROOT / "app" / pages[selection]
if page_file.exists():
    with open(page_file, "r", encoding="utf-8") as f:
        exec(f.read(), {"__file__": str(page_file)})
else:
    st.error(f"Page file not found: {page_file}")