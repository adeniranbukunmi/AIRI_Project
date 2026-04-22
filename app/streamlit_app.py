import sys
from pathlib import Path

import streamlit as st

# Path setup 
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Page config 
st.set_page_config(
    page_title="AIRI — AI Readiness Index",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation 
# spacer removed
st.sidebar.markdown(
    """
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <span style='font-size:1.3rem; font-weight:700; color:#1B3A6B;'>AIRI</span><br>
        <span style='font-size:0.8rem; color:#6B7280;'>AI Readiness Index</span>
    </div>
    """,
    unsafe_allow_html=True,
)

pages = {
    " Assessment":"pages/1_Assessment.py",
    "Cohort Dashboard":"pages/1_Dashboard.py",
    "SHAP Explainer":"pages/3_SHAP_Explainer.py",
    "Benchmarking":"pages/4_Benchmarking.py",
    "About":"pages/5_About.py",
}

st.sidebar.markdown("### Navigation")
selection = st.sidebar.radio(
    "Page",
    list(pages.keys()),
    label_visibility="collapsed",
)



#  Route to selected page
page_file = PROJECT_ROOT / "app" / pages[selection]

if page_file.exists():
    with open(page_file) as f:
        exec(f.read(), {"__file__": str(page_file)})
else:
    st.error(f"Page file not found: {page_file}")
    st.info("Make sure all page files exist in app/pages/")