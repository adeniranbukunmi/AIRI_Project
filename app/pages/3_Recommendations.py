import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.airi_engine import AIRIConfig, AIRIScorer, AIRIRecommender

DIM_SCORE_COLS = ["score_d1", "score_d2", "score_d3", "score_d4", "score_d5"]
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


@st.cache_resource
def load_config():
    return AIRIConfig(str(PROJECT_ROOT / "airi_config.yaml"))


@st.cache_resource
def load_scorer():
    return AIRIScorer(load_config())


@st.cache_resource
def load_recommender():
    return AIRIRecommender(load_config())


def get_scored_row():
    if "assessment_scores" not in st.session_state:
        return None

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
    result = scorer.score_institution(row)
    st.session_state.assessment_result = result
    return pd.Series({**row, **result})


scored = get_scored_row()
if scored is None:
    st.info("Complete the assessment first to generate personalized recommendations.")
    if st.button("Go to Assessment", type="primary"):
        st.session_state.nav_goto = "Assessment"
        st.rerun()
    st.stop()

recs = load_recommender().top_n(scored, n=8)

st.markdown("### Recommendations")
st.caption("Prioritized actions based on your current dimension gap profile.")

for rec in recs:
    priority_color = "#DC2626" if rec["priority_rank"] <= 2 else "#2563EB" if rec["priority_rank"] <= 5 else "#059669"
    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:16px; margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:0.8rem; color:{priority_color}; font-weight:700;">
              Priority {rec["priority_rank"]}
            </span>
            <span style="font-size:0.8rem; color:#6B7280;">
              Gap Score: {rec["gap_score"]:.1f}
            </span>
          </div>
          <div style="font-weight:700; color:#111827;">{rec["dimension"]}</div>
          <div style="margin-top:6px; color:#1F2937;">{rec["action"]}</div>
          <div style="margin-top:8px; color:#6B7280; font-size:0.9rem;">{rec["rationale"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.button("View Results", use_container_width=True):
    st.session_state.nav_goto = "Results"
    st.rerun()
