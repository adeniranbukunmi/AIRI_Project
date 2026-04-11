# app/pages/2_Cohort_Dashboard.py
# ──────────────────────────────────────────────────────────────────────
# AIRI Page 2 — Cohort Dashboard
# Score histogram | Tier donut | Sector bar chart | Dimension heatmap
# ──────────────────────────────────────────────────────────────────────

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Constants ─────────────────────────────────────────────────────────
TIER_COLOURS = {
    "nascent":     "#DC2626",
    "developing":  "#D97706",
    "established": "#059669",
    "leading":     "#1B3A6B",
}
TIER_ORDER  = ["nascent", "developing", "established", "leading"]
DIM_COLS    = ["score_d1","score_d2","score_d3","score_d4","score_d5"]
DIM_LABELS  = ["D1 Data Infra","D2 Tech Maturity",
               "D3 Regulatory","D4 Org Capability","D5 Ethical Gov"]

@st.cache_data
def load_cohort():
    return pd.read_csv(PROJECT_ROOT / "data" / "scored_institutions.csv")

# ── Page header ───────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#1B3A6B;'>📊 Cohort Dashboard</h1>"
    "<p style='color:#6B7280;'>UK debt management institution cohort — 150 synthetic profiles.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

df = load_cohort()

# ── KPI row ───────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Institutions",  len(df))
k2.metric("Mean AIRI Score",     f"{df['airi_score'].mean():.1f}")
k3.metric("% At Leading Tier",
          f"{(df['readiness_tier']=='leading').mean()*100:.1f}%")
k4.metric("% At Nascent Tier",
          f"{(df['readiness_tier']=='nascent').mean()*100:.1f}%")

st.markdown("---")

# ── Row 1: histogram + donut ──────────────────────────────────────────
h_col, d_col = st.columns([1.4, 1], gap="large")

with h_col:
    st.markdown("#### AIRI Score Distribution")
    fig_hist = go.Figure()
    for tier in TIER_ORDER:
        sub = df[df["readiness_tier"] == tier]["airi_score"]
        fig_hist.add_trace(go.Histogram(
            x=sub, name=tier.capitalize(),
            marker_color=TIER_COLOURS[tier],
            opacity=0.85, nbinsx=20,
        ))
    for b in [40, 60, 80]:
        fig_hist.add_vline(x=b, line_dash="dash",
                           line_color="#374151", line_width=1,
                           annotation_text=str(b),
                           annotation_position="top")
    fig_hist.update_layout(
        barmode="stack",
        xaxis_title="AIRI Score (0–100)",
        yaxis_title="Count",
        legend=dict(orientation="h", y=-0.2),
        height=320, margin=dict(t=20,b=60,l=40,r=20),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with d_col:
    st.markdown("#### Readiness Tier Split")
    tier_counts = df["readiness_tier"].value_counts().reindex(TIER_ORDER).fillna(0)
    fig_donut = go.Figure(go.Pie(
        labels=[t.capitalize() for t in TIER_ORDER],
        values=tier_counts.values,
        hole=0.55,
        marker_colors=[TIER_COLOURS[t] for t in TIER_ORDER],
        textinfo="label+percent",
        hoverinfo="label+value",
        textfont_size=11,
    ))
    fig_donut.update_layout(
        showlegend=False,
        height=320, margin=dict(t=20,b=20,l=20,r=20),
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ── Row 2: sector bar + dimension heatmap ────────────────────────────
s_col, hm_col = st.columns([1, 1.6], gap="large")

with s_col:
    st.markdown("#### Mean AIRI Score by Sector")
    sector_means = (df.groupby("sector")["airi_score"]
                      .mean().sort_values(ascending=True))
    fig_sec = go.Figure(go.Bar(
        x=sector_means.values,
        y=[s.replace("_", " ").title() for s in sector_means.index],
        orientation="h",
        marker_color=["#1B3A6B","#0D6E8A","#059669","#D97706"],
        text=[f"{v:.1f}" for v in sector_means.values],
        textposition="outside",
    ))
    fig_sec.update_layout(
        xaxis=dict(range=[0, 100], title="Mean AIRI Score"),
        height=280, margin=dict(t=10,b=40,l=10,r=60),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_sec, use_container_width=True)

with hm_col:
    st.markdown("#### Dimension Score Heatmap by Sector")
    hm_data = df.groupby("sector")[DIM_COLS].mean().round(1)
    hm_data.columns = DIM_LABELS
    fig_hm = go.Figure(go.Heatmap(
        z=hm_data.values,
        x=DIM_LABELS,
        y=[s.replace("_", " ").title() for s in hm_data.index],
        colorscale="YlOrRd",
        zmin=0, zmax=100,
        text=hm_data.values,
        texttemplate="%{text:.1f}",
        textfont=dict(size=12, color="black"),
        hoverongaps=False,
        colorbar=dict(title="Score"),
    ))
    fig_hm.update_layout(
        height=280,
        margin=dict(t=10,b=40,l=10,r=20),
        xaxis=dict(tickangle=-20),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

# ── Institution data table ─────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 🔎 Full Cohort Table")
tier_filter = st.multiselect(
    "Filter by tier:",
    options=TIER_ORDER,
    default=TIER_ORDER,
    format_func=lambda x: x.capitalize(),
)
filtered = df[df["readiness_tier"].isin(tier_filter)] if tier_filter else df
show_cols = ["institution_id","institution_name","sector",
             "institution_size","airi_score","readiness_tier"]
st.dataframe(
    filtered[show_cols].sort_values("airi_score", ascending=False)
                       .reset_index(drop=True),
    use_container_width=True,
    height=300,
)