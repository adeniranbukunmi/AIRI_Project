import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.airi_engine import AIRIConfig, AIRIScorer

DIM_LABELS = [
    "Data Infrastructure",
    "Technological Maturity",
    "Regulatory Compliance",
    "Organisational Capability",
    "Ethical Governance",
]
DIM_SCORE_COLS = ["score_d1", "score_d2", "score_d3", "score_d4", "score_d5"]
DIM_COLORS = ["#3B82F6", "#6366F1", "#8B5CF6", "#A855F7", "#D946EF"]
INDICATOR_KEYS = [
    "data_quality", "data_governance", "data_integration",
    "system_capability", "ai_tooling", "infrastructure_resilience",
    "fca_alignment", "consumer_duty", "audit_trail",
    "talent_readiness", "change_management", "leadership_commitment",
    "bias_mitigation", "explainability", "accountability_structures",
]
QUESTION_TO_INDICATOR = {
    "q01": "data_quality",
    "q02": "data_governance",
    "q03": "data_integration",
    "q04": "data_governance",
    "q05": "data_quality",
    "q06": "system_capability",
    "q07": "ai_tooling",
    "q08": "infrastructure_resilience",
    "q09": "system_capability",
    "q10": "ai_tooling",
    "q11": "fca_alignment",
    "q12": "consumer_duty",
    "q13": "audit_trail",
    "q14": "fca_alignment",
    "q15": "audit_trail",
    "q16": "talent_readiness",
    "q17": "change_management",
    "q18": "leadership_commitment",
    "q19": "leadership_commitment",
    "q20": "talent_readiness",
    "q21": "bias_mitigation",
    "q22": "bias_mitigation",
    "q23": "explainability",
    "q24": "accountability_structures",
    "q25": "accountability_structures",
}

TIER_BADGES = {
    "nascent": "Needs Foundation",
    "developing": "Developing",
    "established": "Good",
    "leading": "Excellent",
}


@st.cache_resource
def load_config():
    return AIRIConfig(str(PROJECT_ROOT / "airi_config.yaml"))


@st.cache_resource
def load_scorer():
    return AIRIScorer(load_config())


def get_result():
    if "assessment_result" in st.session_state:
        return st.session_state.assessment_result

    if "assessment_scores" in st.session_state:
        raw_scores = st.session_state.assessment_scores
        if any(qid not in raw_scores for qid in QUESTION_TO_INDICATOR):
            return None
        if any(raw_scores[qid] < 0 for qid in QUESTION_TO_INDICATOR):
            return None

        indicator_buckets = {k: [] for k in INDICATOR_KEYS}
        for qid, indicator in QUESTION_TO_INDICATOR.items():
            indicator_buckets[indicator].append(max(int(raw_scores[qid]), 1))

        indicator_scores = {}
        for indicator, values in indicator_buckets.items():
            indicator_scores[indicator] = int(round(sum(values) / len(values))) if values else 1

        scorer = load_scorer()
        row = pd.Series(
            {
                **indicator_scores,
                "institution_id": "ASSESSMENT",
                "institution_name": "Your Institution",
                "sector": "retail_bank",
                "institution_size": "mid",
            }
        )
        return scorer.score_institution(row)
    return None


result = get_result()
if result is None:
    st.info("No completed assessment yet. Go to **Assessment** and calculate results first.")
    if st.button("Go to Assessment", type="primary"):
        st.session_state.nav_goto = "Assessment"
        st.rerun()
    st.stop()

overall = result["airi_score"]
tier = result["readiness_tier"]
dim_scores = [result[c] for c in DIM_SCORE_COLS]
best_idx = max(range(len(dim_scores)), key=lambda i: dim_scores[i])

left_top, right_top = st.columns([1, 1.7], gap="large")
with left_top:
    st.markdown("### Assessment Results")
    st.caption("Completed in current session")
with right_top:
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("Retake Assessment", use_container_width=True):
            st.session_state.nav_goto = "Assessment"
            st.rerun()
    with b2:
        st.download_button(
            "Export Report (JSON)",
            data=str(result),
            file_name="airi_results.txt",
            use_container_width=True,
        )

a, b = st.columns([1, 2], gap="large")
with a:
    st.markdown(
        f"""
        <div style="background:#EEF2FF; border:1px solid #E5E7EB; border-radius:14px; padding:18px;">
          <div style="color:#374151; font-size:0.9rem;">Overall Readiness Score</div>
          <div style="font-size:3rem; font-weight:700; color:#111827; line-height:1.1;">{overall:.0f}</div>
          <span style="background:#DBEAFE; color:#1E40AF; border-radius:999px; padding:4px 10px; font-size:0.8rem;">
            {TIER_BADGES.get(tier, tier.title())}
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with b:
    fig = go.Figure(
        go.Bar(
            x=DIM_LABELS,
            y=dim_scores,
            marker_color=DIM_COLORS,
        )
    )
    fig.update_layout(
        title="Dimension Breakdown",
        yaxis=dict(range=[0, 100], title="Score"),
        height=280,
        margin=dict(t=45, b=10, l=30, r=15),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

r1, r2 = st.columns(2, gap="large")
with r1:
    radar = go.Figure()
    radar.add_trace(
        go.Scatterpolar(
            r=dim_scores + [dim_scores[0]],
            theta=DIM_LABELS + [DIM_LABELS[0]],
            fill="toself",
            line=dict(color="#3B82F6", width=2),
            fillcolor="#93C5FD",
            opacity=0.5,
            name="Readiness Profile",
        )
    )
    radar.update_layout(
        title="Readiness Profile",
        polar=dict(radialaxis=dict(range=[0, 100])),
        height=360,
        margin=dict(t=50, b=20, l=25, r=25),
    )
    st.plotly_chart(radar, use_container_width=True)
with r2:
    st.markdown("#### Key Insights")
    for idx, (label, score) in enumerate(sorted(zip(DIM_LABELS, dim_scores), key=lambda x: x[1], reverse=True)):
        st.markdown(
            f"""
            <div style="margin-bottom:10px;">
              <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
                <span>{label}</span><strong>{score:.0f}%</strong>
              </div>
              <div style="background:#E5E7EB; border-radius:8px; height:8px;">
                <div style="width:{int(score)}%; height:8px; border-radius:8px; background:{DIM_COLORS[idx]};"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("#### Detailed Dimension Analysis")
tiles = st.columns(5)
for tile, name, score in zip(tiles, DIM_LABELS, dim_scores):
    tile.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:12px; padding:14px;">
          <div style="font-size:0.82rem; color:#374151;">{name}</div>
          <div style="font-size:1.8rem; font-weight:700; color:#111827;">{score:.0f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(f"Strongest dimension: {DIM_LABELS[best_idx]}")
