import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.airi_engine import AIRIConfig, AIRIScorer

DIMENSION_ORDER = [
    "Data",
    "Technological",
    "Regulatory",
    "Organisational",
    "Ethical",
]

DIMENSIONS = {
    "Data": {
        "title": "Data Infrastructure",
        "items": [
            {"id": "q01", "indicator": "data_quality", "question": "Our organization has centralized, accessible data repositories with clear data governance policies."},
            {"id": "q02", "indicator": "data_governance", "question": "We have established data quality metrics and regularly audit data accuracy, completeness, and consistency."},
            {"id": "q03", "indicator": "data_integration", "question": "Our data infrastructure supports real-time data processing and integration across systems."},
            {"id": "q04", "indicator": "data_governance", "question": "Data ownership and stewardship roles are clearly defined across business and technology teams."},
            {"id": "q05", "indicator": "data_quality", "question": "We have proactive controls to detect and resolve missing, inconsistent, or duplicate data before model use."},
        ],
    },
    "Technological": {
        "title": "Technological Maturity",
        "items": [
            {"id": "q06", "indicator": "system_capability", "question": "Our AI systems are deployed on scalable infrastructure that supports production workloads."},
            {"id": "q07", "indicator": "ai_tooling", "question": "We use established ML tooling and model lifecycle practices for development and monitoring."},
            {"id": "q08", "indicator": "infrastructure_resilience", "question": "We have tested resilience and disaster recovery plans for AI services."},
            {"id": "q09", "indicator": "system_capability", "question": "AI models are monitored for performance degradation and operational health in production."},
            {"id": "q10", "indicator": "ai_tooling", "question": "Our model deployment process is automated and repeatable across environments."},
        ],
    },
    "Regulatory": {
        "title": "Regulatory Compliance",
        "items": [
            {"id": "q11", "indicator": "fca_alignment", "question": "Our AI governance framework aligns with FCA guidance and internal compliance standards."},
            {"id": "q12", "indicator": "consumer_duty", "question": "Consumer Duty requirements are explicitly mapped to AI use cases and monitored."},
            {"id": "q13", "indicator": "audit_trail", "question": "AI decisions are captured with an auditable and retrievable trail."},
            {"id": "q14", "indicator": "fca_alignment", "question": "Regulatory obligations are reviewed and updated as part of model lifecycle governance."},
            {"id": "q15", "indicator": "audit_trail", "question": "We can provide end-to-end evidence for how an AI-assisted decision was made."},
        ],
    },
    "Organisational": {
        "title": "Organisational Capability",
        "items": [
            {"id": "q16", "indicator": "talent_readiness", "question": "Our organization has dedicated teams or roles responsible for AI strategy and implementation."},
            {"id": "q17", "indicator": "change_management", "question": "We have established change management processes to support AI adoption across the organization."},
            {"id": "q18", "indicator": "leadership_commitment", "question": "Our staff receive regular training on AI literacy, data skills, and responsible AI practices."},
            {"id": "q19", "indicator": "leadership_commitment", "question": "Leadership demonstrates commitment to AI initiatives with clear vision and allocated resources."},
            {"id": "q20", "indicator": "talent_readiness", "question": "We have cross-functional collaboration between IT, risk, compliance, and business units for AI projects."},
        ],
    },
    "Ethical": {
        "title": "Ethical Governance",
        "items": [
            {"id": "q21", "indicator": "bias_mitigation", "question": "Our organization has established AI ethics principles and guidelines aligned with industry standards."},
            {"id": "q22", "indicator": "bias_mitigation", "question": "We conduct fairness and bias assessments for AI models before deployment."},
            {"id": "q23", "indicator": "explainability", "question": "Our AI systems include explainability features and documentation for stakeholder understanding."},
            {"id": "q24", "indicator": "accountability_structures", "question": "We have governance structures (e.g., AI ethics committee) to oversee responsible AI deployment."},
            {"id": "q25", "indicator": "accountability_structures", "question": "Our organization has processes for ongoing monitoring of AI system impacts on vulnerable customers."},
        ],
    },
}

INDICATOR_KEYS = [
    "data_quality", "data_governance", "data_integration",
    "system_capability", "ai_tooling", "infrastructure_resilience",
    "fca_alignment", "consumer_duty", "audit_trail",
    "talent_readiness", "change_management", "leadership_commitment",
    "bias_mitigation", "explainability", "accountability_structures",
]
QUESTION_IDS = [
    q["id"]
    for dim in DIMENSION_ORDER
    for q in DIMENSIONS[dim]["items"]
]

st.markdown(
    """
    <style>
    .assessment-end-label {
        font-size: 0.76rem;
        color: #6B7280;
        white-space: nowrap;
    }
    .assessment-end-label-wrap {
        height: 2.2rem;
        display: flex;
        align-items: center;
    }
    .assessment-end-label-wrap.left {
        justify-content: flex-end;
        padding-right: 0.35rem;
    }
    .assessment-end-label-wrap.right {
        justify-content: flex-start;
        padding-left: 0.35rem;
    }
    [data-testid="stPills"] [role="radiogroup"] {
        display: flex !important;
        gap: 8px !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
    }
    [data-testid="stPills"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stPills"] [role="radio"] {
        min-width: 56px !important;
        height: 42px !important;
        margin: 0 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 0 !important;
        background: #FFFFFF !important;
        color: #374151 !important;
        justify-content: center !important;
        box-shadow: none !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stPills"] button {
        min-width: 56px !important;
        height: 42px !important;
        padding: 0 14px !important;
        border-radius: 0 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stPills"] button p {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stPills"] [role="radio"][aria-checked="true"] {
        background: #2563EB !important;
        border-color: #2563EB !important;
        color: #FFFFFF !important;
    }
    [data-testid="stPills"] [role="radio"]:hover {
        border-color: #93C5FD !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_config():
    return AIRIConfig(str(PROJECT_ROOT / "airi_config.yaml"))


@st.cache_resource
def load_scorer():
    return AIRIScorer(load_config())


def get_progress(scores_dict):
    answered = sum(1 for v in scores_dict.values() if v >= 0)
    return answered


if "assessment_scores" not in st.session_state or set(st.session_state.assessment_scores.keys()) != set(QUESTION_IDS):
    st.session_state.assessment_scores = {qid: -1 for qid in QUESTION_IDS}
if "assessment_dim_idx" not in st.session_state:
    st.session_state.assessment_dim_idx = 0
if "assessment_dimension_picker" not in st.session_state:
    st.session_state.assessment_dimension_picker = DIMENSION_ORDER[st.session_state.assessment_dim_idx]

# Apply one-shot dimension navigation requests BEFORE rendering the picker widget.
if "assessment_dim_goto" in st.session_state:
    goto_idx = max(0, min(int(st.session_state.assessment_dim_goto), len(DIMENSION_ORDER) - 1))
    st.session_state.assessment_dim_idx = goto_idx
    st.session_state.assessment_dimension_picker = DIMENSION_ORDER[goto_idx]
    del st.session_state.assessment_dim_goto

scores = st.session_state.assessment_scores

answered_count = sum(1 for v in scores.values() if v >= 0)
progress_pct = answered_count / len(QUESTION_IDS)

st.markdown("### Assessment Progress")
st.progress(progress_pct)
st.caption(f"{answered_count} / {len(QUESTION_IDS)} questions answered")

selected_dim = st.radio(
    "Assessment Dimension",
    DIMENSION_ORDER,
    horizontal=True,
    key="assessment_dimension_picker",
    label_visibility="collapsed",
)
st.session_state.assessment_dim_idx = DIMENSION_ORDER.index(selected_dim)

dim_cfg = DIMENSIONS[selected_dim]
st.markdown(f"## {dim_cfg['title']}")
st.caption("Rate your organization's capabilities on a scale of 0 (not at all) to 5 (fully implemented).")

for idx, item in enumerate(dim_cfg["items"], start=1):
    qid = item["id"]
    question = item["question"]
    st.markdown(f"**{idx}. {question}**")
    gutter_left, compact_row, gutter_right = st.columns([1.9, 4.2, 1.9])
    with compact_row:
        left, middle, right = st.columns([1.0, 3.2, 1.0], vertical_alignment="center")
        with left:
            st.markdown(
                "<div class='assessment-end-label-wrap left'>"
                "<span class='assessment-end-label'>Not at all</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        with middle:
            widget_key = f"q_{qid}"
            if widget_key not in st.session_state and scores[qid] >= 0:
                # Restore previously selected value when returning to this dimension.
                st.session_state[widget_key] = scores[qid]
            st.pills(
                f"{selected_dim}-{idx}",
                options=[0, 1, 2, 3, 4, 5],
                selection_mode="single",
                label_visibility="collapsed",
                key=widget_key,
            )
            current = st.session_state.get(widget_key, scores[qid] if scores[qid] >= 0 else None)
        with right:
            st.markdown(
                "<div class='assessment-end-label-wrap right'>"
                "<span class='assessment-end-label'>Fully implemented</span>"
                "</div>",
                unsafe_allow_html=True,
            )
    # Be defensive: single-mode pills may store scalar or list.
    if isinstance(current, list):
        current = current[0] if current else None

    if current is None:
        scores[qid] = -1
    else:
        scores[qid] = int(current)
    st.divider()

all_answered = all(v >= 0 for v in scores.values())
is_last_dimension = st.session_state.assessment_dim_idx == (len(DIMENSION_ORDER) - 1)

c1, c2, c3 = st.columns([1, 3.2, 1])
with c1:
    if st.button("Previous", use_container_width=True):
        new_idx = max(st.session_state.assessment_dim_idx - 1, 0)
        st.session_state.assessment_dim_goto = new_idx
        st.rerun()
with c2:
    st.markdown("&nbsp;", unsafe_allow_html=True)
with c3:
    if is_last_dimension:
        if st.button(
            "Calculate Results",
            type="primary",
            use_container_width=True,
            disabled=not all_answered,
        ):
            scorer = load_scorer()
            indicator_buckets = {k: [] for k in INDICATOR_KEYS}
            for dim in DIMENSION_ORDER:
                for item in DIMENSIONS[dim]["items"]:
                    raw_value = scores[item["id"]]
                    indicator_buckets[item["indicator"]].append(max(raw_value, 1))

            indicator_scores = {}
            for indicator, values in indicator_buckets.items():
                if values:
                    indicator_scores[indicator] = int(round(sum(values) / len(values)))
                else:
                    indicator_scores[indicator] = 1

            assessment_row = pd.Series(
                {
                    **indicator_scores,
                    "institution_id": "ASSESSMENT",
                    "institution_name": "Your Institution",
                    "sector": "retail_bank",
                    "institution_size": "mid",
                }
            )
            result = scorer.score_institution(assessment_row)
            st.session_state.assessment_result = result
            st.session_state.nav_goto = "Results"
            st.rerun()
    else:
        if st.button("Next Dimension", use_container_width=True):
            new_idx = min(st.session_state.assessment_dim_idx + 1, len(DIMENSION_ORDER) - 1)
            st.session_state.assessment_dim_goto = new_idx
            st.rerun()