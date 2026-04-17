import streamlit as st

CARD_STYLE = (
    "background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; "
    "padding:18px; height:100%;"
)

st.markdown(
    """
    <style>
    .airi-hero-card {
        position: relative;
        overflow: hidden;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 14px;
    }
    .airi-hero-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #2563EB 0%, #60A5FA 100%);
    }
    .airi-hero-motif {
        position: absolute;
        right: 22px;
        top: 18px;
        display: flex;
        gap: 8px;
        opacity: 0.95;
    }
    .airi-hero-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: #BFDBFE;
        border: 1px solid #93C5FD;
    }
    .airi-hero-dot:nth-child(2) { background: #93C5FD; }
    .airi-hero-dot:nth-child(3) { background: #60A5FA; }
    .stButton > button {
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: 1px solid #2563EB !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
        color: #FFFFFF !important;
    }
    .stButton > button:focus {
        box-shadow: 0 0 0 0.2rem rgba(37, 99, 235, 0.25) !important;
    }
    .airi-hero-title {
        margin: 0;
        color: #111827 !important;
        font-size: 2.1rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .airi-hero-copy {
        margin-top: 8px;
        color: #374151 !important;
        font-size: 1rem;
        max-width: 760px;
    }
    .airi-icon-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 10px;
        margin-right: 8px;
        background: linear-gradient(145deg, #EFF6FF, #F5F3FF);
        border: 1px solid #E5E7EB;
        font-size: 1.25rem;
    }
    .airi-card-title {
        font-weight: 700;
        color: #111827 !important;
        margin: 10px 0 6px 0;
    }
    .airi-card-desc {
        font-size: 0.84rem;
        color: #4B5563 !important;
        line-height: 1.45;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown(
        """
        <div style="position:relative;">
          <div class="airi-hero-motif">
            <span class="airi-hero-dot"></span>
            <span class="airi-hero-dot"></span>
            <span class="airi-hero-dot"></span>
          </div>
          <h2 class="airi-hero-title">AI Readiness Assessment for Financial Services</h2>
          <p class="airi-hero-copy">
            Evaluate your organization's preparedness for deploying AI agents in debt management
            with our comprehensive readiness framework.
          </p>
          <div style="margin-top:8px; margin-bottom:10px;">
            <span class="airi-icon-pill">🛡️</span>
            <span class="airi-icon-pill">🗄️</span>
            <span class="airi-icon-pill">⚙️</span>
            <span class="airi-icon-pill">⚖️</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cta_col, _ = st.columns([1, 3.5])
    with cta_col:
        if st.button("Start Assessment", type="primary", use_container_width=True):
            st.session_state.nav_goto = "Assessment"
            st.rerun()

st.markdown("")
c1, c2, c3, c4, c5 = st.columns(5)

cards = [
    ("🗄️", "Data Infrastructure", "Data governance, quality, and infrastructure"),
    ("⚙️", "Technological Maturity", "IT capabilities and ML operations"),
    ("⚖️", "Regulatory Compliance", "FCA compliance and audit frameworks"),
    ("✅", "Organisational Capability", "Skills, team, and change management"),
    ("🛡️", "Ethical Governance", "Ethics, fairness, and transparency"),
]

for col, (icon, title, desc) in zip([c1, c2, c3, c4, c5], cards):
    with col:
        st.markdown(
            f"""
            <div style="{CARD_STYLE}">
              <div class="airi-icon-pill">{icon}</div>
              <div class="airi-card-title">{title}</div>
              <div class="airi-card-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("")
st.markdown(
    f"""
    <div style="{CARD_STYLE}">
      <h3 style="margin-top:0; color:#111827;">About the AI Readiness Index</h3>
      <div style="display:flex; gap:36px;">
        <div style="flex:1;">
          <h4 style="margin:4px 0; color:#1F2937;">Purpose</h4>
          <p style="font-size:0.92rem; color:#4B5563;">
            AIRI provides a quantitative assessment of your institution's readiness for responsible AI
            adoption across data, technology, regulation, organization, and ethics.
          </p>
        </div>
        <div style="flex:1;">
          <h4 style="margin:4px 0; color:#1F2937;">Methodology</h4>
          <p style="font-size:0.92rem; color:#4B5563;">
            The scoring engine applies weighted indicators to produce dimension scores and a single
            composite index from 0 to 100, mapped into readiness tiers.
          </p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)