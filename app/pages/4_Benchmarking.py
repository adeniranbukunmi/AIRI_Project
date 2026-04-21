# app/pages/4_Benchmarking.py
# AIRI Page 4 — Benchmarking
# Enter custom scores → compare against sector peers and UK cohort
# average; percentile rank displayed


import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.airi_engine import AIRIConfig, AIRIScorer

TIER_COLOURS = {
    "nascent": "#DC2626","developing": "#D97706",
    "established": "#059669","leading": "#1B3A6B",
}
TIER_ORDER = ["nascent","developing","established","leading"]
DIM_COLS   = ["score_d1","score_d2","score_d3","score_d4","score_d5"]
DIM_LABELS = ["Data Infrastructure","Technological Maturity",
              "Regulatory Compliance","Organisational Capability","Ethical Governance"]
INDICATOR_COLS = [
    "data_quality","data_governance","data_integration",
    "system_capability","ai_tooling","infrastructure_resilience",
    "fca_alignment","consumer_duty","audit_trail",
    "talent_readiness","change_management","leadership_commitment",
    "bias_mitigation","explainability","accountability_structures",
]

@st.cache_resource
def load_config():  return AIRIConfig(str(PROJECT_ROOT / "airi_config.yaml"))
@st.cache_resource
def load_scorer():  return AIRIScorer(load_config())
@st.cache_data
def load_cohort():  return pd.read_csv(PROJECT_ROOT / "data" / "scored_institutions.csv")

# Page header 
st.markdown(
    "<h1 style='color:#1B3A6B;'> Benchmarking</h1>"
    "<p style='color:#6B7280;'>Compare your institution against sector "
    "peers and the UK cohort average.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

df      = load_cohort()
scorer  = load_scorer()
config  = load_config()

# Inputs 
inp_col, res_col = st.columns([1, 1.6], gap="large")

with inp_col:
    st.markdown("### Your Institution")
    inst_name = st.text_input("Institution name (optional)", value="My Institution")
    sector    = st.selectbox("Sector", ["retail_bank","debt_purchaser", "fintech_lender","credit_union"],
    format_func=lambda x: x.replace("_"," ").title())
    inst_size = st.selectbox("Size", ["large","mid","small"],
    format_func=str.capitalize)
    st.markdown("**Indicator scores (1–5):**")
    scores = {}
    for ind in INDICATOR_COLS:
        scores[ind] = st.slider(
            ind.replace("_"," ").title(), 1, 5, 3,
            key=f"bench_{ind}"
        )

#  Score this institution 
row = pd.Series({
    **scores,
    "institution_id": "BENCH",
    "institution_name": inst_name,
    "sector": sector,
    "institution_size": inst_size,
})
result     = scorer.score_institution(row)
airi_score = result["airi_score"]
tier       = result["readiness_tier"]
dim_scores = [result[c] for c in DIM_COLS]

# Peer group stats 
peer_df      = df[df["sector"] == sector]
cohort_means = df[DIM_COLS].mean().values
peer_means   = peer_df[DIM_COLS].mean().values

# Percentile rank in full cohort
pct_rank = round((df["airi_score"] < airi_score).mean() * 100, 1)
peer_pct = round((peer_df["airi_score"] < airi_score).mean() * 100, 1)

with res_col:
    # Score + tier badge 
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Your AIRI Score",   f"{airi_score:.1f}")
    m2.metric("Cohort Percentile", f"{pct_rank}th")
    m3.metric("Sector Percentile", f"{peer_pct}th")
    m4.markdown(
        f"<div style='background:{TIER_COLOURS[tier]};color:white;"
        f"border-radius:20px;padding:10px;text-align:center;"
        f"font-weight:700;margin-top:8px;'>{tier.upper()}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Radar: you vs sector peers vs cohort 
    st.markdown("#### Dimension Radar — You vs Peers vs Cohort")
    radar_labels = ["Data\nInfra","Tech\nMaturity","Regulatory",
                    "Org\nCapability","Ethical\nGov"]
    angles = radar_labels + [radar_labels[0]]

    fig_r = go.Figure()
    for vals, name, colour, dash in [
        (dim_scores,        "Your Institution",       TIER_COLOURS[tier], "solid"),
        (list(peer_means),  f"{sector.replace('_',' ').title()} Peers", "#0D6E8A", "dash"),
        (list(cohort_means),"UK Cohort Average",      "#9CA3AF",          "dot"),
    ]:
        v = vals + [vals[0]]
        fig_r.add_trace(go.Scatterpolar(
            r=v, theta=angles, fill="toself", name=name,
            line=dict(color=colour, width=2, dash=dash),
            fillcolor=colour, opacity=0.12,
        ))
    fig_r.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100],
                                   tickfont=dict(size=8))),
        legend=dict(orientation="h", y=-0.15),
        height=320, margin=dict(t=20,b=50,l=40,r=40),
    )
    st.plotly_chart(fig_r, use_container_width=True)

    # Grouped bar: dimension scores vs peer avg 
    st.markdown("#### Dimension Score Comparison")
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Your Institution", x=DIM_LABELS, y=dim_scores,
        marker_color=TIER_COLOURS[tier], text=[f"{v:.1f}" for v in dim_scores],
        textposition="outside",
    ))
    fig_bar.add_trace(go.Bar(
        name=f"{sector.replace('_',' ').title()} Peers",
        x=DIM_LABELS, y=peer_means,
        marker_color="#0D6E8A", opacity=0.7,
        text=[f"{v:.1f}" for v in peer_means],
        textposition="outside",
    ))
    fig_bar.add_trace(go.Bar(
        name="UK Cohort Average", x=DIM_LABELS, y=cohort_means,
        marker_color="#9CA3AF", opacity=0.7,
        text=[f"{v:.1f}" for v in cohort_means],
        textposition="outside",
    ))
    fig_bar.update_layout(
        barmode="group",
        yaxis=dict(range=[0,115], title="Score (0–100)"),
        height=320,
        legend=dict(orientation="h", y=-0.25),
        margin=dict(t=10,b=80,l=40,r=20),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Percentile gauge
st.markdown("---")
g1, g2 = st.columns(2)

for col, rank, title in [
    (g1, pct_rank,  "UK Cohort Percentile Rank"),
    (g2, peer_pct,  f"{sector.replace('_',' ').title()} Sector Percentile"),
]:
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rank,
        number={"suffix": "th", "font": {"size": 36, "color": "#1B3A6B"}},
        gauge=dict(
            axis=dict(range=[0,100]),
            bar=dict(color=TIER_COLOURS[tier]),
            steps=[
                dict(range=[0,25],  color="#FEE2E2"),
                dict(range=[25,50], color="#FEF3C7"),
                dict(range=[50,75], color="#D1FAE5"),
                dict(range=[75,100],color="#DBEAFE"),
            ],
        ),
        title={"text": title, "font": {"size": 13}},
    ))
    fig_g.update_layout(height=220, margin=dict(t=40,b=10,l=30,r=30))
    col.plotly_chart(fig_g, use_container_width=True)

# Top/bottom 5 in sector 
st.markdown("---")
t_col, b_col = st.columns(2)
show_cols = ["institution_id","institution_name","airi_score","readiness_tier"]

with t_col:
    st.markdown(f"**Top 5 in {sector.replace('_',' ').title()}**")
    st.dataframe(
        peer_df.nlargest(5,"airi_score")[show_cols].reset_index(drop=True),
        use_container_width=True,
    )
with b_col:
    st.markdown(f"**Bottom 5 in {sector.replace('_',' ').title()}**")
    st.dataframe(
        peer_df.nsmallest(5,"airi_score")[show_cols].reset_index(drop=True),
        use_container_width=True,
    )