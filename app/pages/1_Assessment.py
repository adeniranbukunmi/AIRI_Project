# app/pages/1_Assessment.py
# AIRI Page 1 — Assessment
# 15 sliders → live AIRI score + tier badge + radar chart +
# dimension table + top 3 recommendations + SHAP waterfall
# 

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Path & imports 
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.airi_engine import AIRIConfig, AIRIScorer, AIRIRecommender
from src.xgb_explain import explain_instance, load_xgb_classifier

#  Cached resource loaders 
@st.cache_resource
def load_config():
    return AIRIConfig(str(PROJECT_ROOT / "airi_config.yaml"))

@st.cache_resource
def load_scorer():
    return AIRIScorer(load_config())

@st.cache_resource
def load_recommender():
    return AIRIRecommender(load_config())

@st.cache_resource
def load_xgb_model():
    return load_xgb_classifier(PROJECT_ROOT)

@st.cache_data
def load_cohort():
    return pd.read_csv(PROJECT_ROOT / "data" / "scored_institutions.csv")

# Tier colour map (spec Section 7.3) 
TIER_COLOURS = {
    "nascent":     "#DC2626",
    "developing":  "#D97706",
    "established": "#059669",
    "leading":     "#1B3A6B",
}

# Indicator tooltips (scoring guidance from spec Sections 3.2–3.6) ─
TOOLTIPS = {
    "data_quality":
        "1 = No data quality controls.\n"
        "3 = Periodic quality checks exist.\n"
        "5 = Automated real-time data quality monitoring with SLAs.",
    "data_governance":
        "1 = No formal governance.\n"
        "3 = Data governance policy exists but inconsistently applied.\n"
        "5 = Mature governance with data stewards, lineage tracking, and audit trails.",
    "data_integration":
        "1 = Siloed systems, manual exports.\n"
        "3 = Partial API integrations.\n"
        "5 = Unified data platform with real-time integration across all operational systems.",
    "system_capability":
        "1 = No ML infrastructure.\n"
        "3 = Ad hoc ML experimentation exists.\n"
        "5 = Production ML platform with CI/CD, model registries, and monitoring.",
    "ai_tooling":
        "1 = No AI tools deployed.\n"
        "3 = Some ML libraries used in isolated projects.\n"
        "5 = Mature MLOps stack with automated retraining and drift detection.",
    "infrastructure_resilience":
        "1 = No resilience planning for AI.\n"
        "3 = Basic DR plans.\n"
        "5 = Fully tested resilience framework covering AI workloads with documented RTO/RPO.",
    "fca_alignment":
        "1 = No awareness of FCA AI guidance (DP5/22).\n"
        "3 = Partial alignment.\n"
        "5 = Full documented alignment with FCA principles; internal compliance reviews completed.",
    "consumer_duty":
        "1 = Consumer Duty obligations not mapped to AI processes.\n"
        "3 = Mapping in progress.\n"
        "5 = All AI touchpoints audited against Consumer Duty; outcomes monitoring in place.",
    "audit_trail":
        "1 = No audit capability for AI decisions.\n"
        "3 = Manual audit logs.\n"
        "5 = Automated, immutable audit trail for all AI-influenced decisions with retrieval SLA.",
    "talent_readiness":
        "1 = No AI skills internally.\n"
        "3 = Small AI team; limited broader literacy.\n"
        "5 = Organisation-wide AI literacy programme; dedicated AI governance roles.",
    "change_management":
        "1 = No structured change process for AI adoption.\n"
        "3 = Ad hoc change management.\n"
        "5 = Formal AI change management framework with stakeholder engagement.",
    "leadership_commitment":
        "1 = AI not on senior leadership agenda.\n"
        "3 = Executive sponsor identified.\n"
        "5 = AI strategy owned at board level; dedicated AI investment budget; KPIs tracked.",
    "bias_mitigation":
        "1 = No bias awareness.\n"
        "3 = Ad hoc bias checks on some models.\n"
        "5 = Systematic bias testing framework (pre/post-deployment) with documented remediation.",
    "explainability":
        "1 = Black-box AI with no explanation capability.\n"
        "3 = Some XAI methods used.\n"
        "5 = SHAP/LIME applied to all customer-facing AI; explanations logged.",
    "accountability_structures":
        "1 = No formal AI accountability.\n"
        "3 = Responsibility assigned informally.\n"
        "5 = Documented accountability framework; named AI owner per system; escalation paths.",
}

# Dimension metadata 
DIMENSIONS = {
    "Data Infrastructure":       ["data_quality", "data_governance", "data_integration"],
    "Technological Maturity":    ["system_capability", "ai_tooling", "infrastructure_resilience"],
    "Regulatory Compliance":     ["fca_alignment", "consumer_duty", "audit_trail"],
    "Organisational Capability": ["talent_readiness", "change_management", "leadership_commitment"],
    "Ethical Governance":        ["bias_mitigation", "explainability", "accountability_structures"],
}
DIM_SCORE_COLS = ["score_d1", "score_d2", "score_d3", "score_d4", "score_d5"]
FEATURE_COLS = list(TOOLTIPS.keys()) + ["sector_enc", "size_enc"]


# PAGE LAYOUT
st.markdown(
    "<h1 style='color:#1B3A6B; margin-bottom:0;'>Institutionss Assessment</h1>"
    "<p style='color:#1B3A6B; margin-top:4px;'>"
    "Set each indicator score (1-5) to compute your institution's AIRI readiness profile in real-time.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# Load resources 
config      = load_config()
scorer      = load_scorer()
recommender = load_recommender()
cohort_df   = load_cohort()

try:
    xgb_model = load_xgb_model()
    shap_available = True
except Exception:
    shap_available = False

cohort_dim_means = cohort_df[DIM_SCORE_COLS].mean().values

# Two-column layout: sliders left, results right 
col_sliders, col_results = st.columns([1, 1.6], gap="large")

# LEFT: Indicator sliders grouped by dimension 
with col_sliders:
    st.markdown("### Indicator Scores")
    st.caption("Expand each dimension and rate your institution 1–5.")

    slider_values = {}
    for dim_name, indicators in DIMENSIONS.items():
        with st.expander(f"**{dim_name}**", expanded=False):
            for ind in indicators:
                label = ind.replace("_", " ").title()
                slider_values[ind] = st.slider(
                    label=label,
                    min_value=1,
                    max_value=5,
                    value=3,
                    step=1,
                    help=TOOLTIPS[ind],
                    key=f"slider_{ind}",
                )

# Score this institution 
input_row = pd.Series({
    **slider_values,
    "institution_id":   "ASSESSMENT",
    "institution_name": "Your Institution",
    "sector":           "retail_bank",
    "institution_size": "mid",
})
score_result = scorer.score_institution(input_row)
scored_row   = pd.Series({**input_row, **score_result})

airi_score    = score_result["airi_score"]
tier          = score_result["readiness_tier"]
tier_colour   = TIER_COLOURS[tier]
dim_scores    = [score_result[c] for c in DIM_SCORE_COLS]

# RIGHT: Results 
with col_results:

    # AIRI Score metric + tier badge 
    r1, r2 = st.columns([1, 1])
    with r1:
        st.metric(
            label="AIRI Composite Score",
            value=f"{airi_score:.1f} / 100",
            delta=f"{airi_score - cohort_df['airi_score'].mean():.1f} vs cohort avg",
        )
    with r2:
        st.markdown(
            f"<div style='"
            f"background:{tier_colour}; color:white; border-radius:24px;"
            f"padding:14px 20px; text-align:center; margin-top:8px;"
            f"font-size:1.1rem; font-weight:700; letter-spacing:1px;'>"
            f"{tier.upper()}"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Radar chart: this institution vs cohort average 
    radar_labels = ["Data\nInfra", "Tech\nMaturity",
                    "Regulatory", "Org\nCapability", "Ethical\nGov"]
    angles = list(radar_labels) + [radar_labels[0]]
    inst_vals   = dim_scores + [dim_scores[0]]
    cohort_vals = list(cohort_dim_means) + [cohort_dim_means[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=inst_vals, theta=angles,
        fill="toself", name="Your Institution",
        line=dict(color=tier_colour, width=2.5),
        fillcolor=tier_colour, opacity=0.25,
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=cohort_vals, theta=angles,
        fill="toself", name="Cohort Average",
        line=dict(color="#FFFFFF", width=1.5, dash="dash"),
        fillcolor="#FFFFFF", opacity=0.10,
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=9)),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        margin=dict(t=30, b=40, l=40, r=40),
        height=320,
        title=dict(text="Dimension Scores vs Cohort Average",
                   font=dict(size=13, color="#FFFFFF")),
    )
    fig_radar.update_layout(
    font=dict(color="black"),  
    paper_bgcolor='rgba(0,0,0,0)', 
    plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    #  Dimension score table with progress bars 
    st.markdown("####  Dimension Breakdown")
    for i, (dim_name, score) in enumerate(
        zip(list(DIMENSIONS.keys()), dim_scores)
    ):
        gap       = 100 - score
        bar_pct   = int(score)
        bar_html  = (
            f"<div style='background:#E5E7EB; border-radius:4px; height:10px; width:100%;'>"
            f"<div style='background:{tier_colour}; width:{bar_pct}%; "
            f"height:10px; border-radius:4px;'></div></div>"
        )
        st.markdown(
            f"<div style='display:flex; justify-content:space-between; "
            f"font-size:0.85rem; margin-bottom:2px;'>"
            f"<span style='color:#374151;'>{dim_name}</span>"
            f"<span style='font-weight:700; color:{tier_colour};'>"
            f"{score:.1f}</span></div>"
            f"{bar_html}<div style='margin-bottom:8px;'></div>",
            unsafe_allow_html=True,
        )


# FULL WIDTH: Recommendations + SHAP 
st.markdown("---")
rec_col, shap_col = st.columns([1, 1], gap="large")

# Top 3 recommendations 
with rec_col:
    st.markdown("#### Top 3 Priority Recommendations")
    top3 = recommender.top_n(scored_row, n=3)
    priority_colours = ["#DC2626", "#D97706", "#059669"]
    for rec in top3:
        rank_colour = priority_colours[rec["priority_rank"] - 1]
        st.markdown(
            f"<div style='border-left: 4px solid {rank_colour}; "
            f"background:#F9FAFB; border-radius:6px; "
            f"padding:12px 16px; margin-bottom:12px;'>"
            f"<div style='font-size:0.75rem; color:{rank_colour}; "
            f"font-weight:700; text-transform:uppercase; letter-spacing:0.5px;'>"
            f"Priority {rec['priority_rank']} — {rec['dimension']} "
            f"(Gap: {rec['gap_score']:.0f})</div>"
            f"<div style='font-size:0.9rem; font-weight:600; "
            f"color:#111827; margin:6px 0 4px 0;'>{rec['action']}</div>"
            f"<div style='font-size:0.82rem; color:#6B7280;'>{rec['rationale']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

# SHAP waterfall 
with shap_col:
    st.markdown("#### SHAP Feature Contributions")
    if not shap_available:
        st.info("XGBoost model not found. Run Notebook 03 first to generate models/xgb_model.pkl")
    else:
        try:
            from sklearn.preprocessing import LabelEncoder
            sector_enc = LabelEncoder().fit(
                ["credit_union", "debt_purchaser", "fintech_lender", "retail_bank"]
            ).transform(["retail_bank"])[0]
            size_enc = LabelEncoder().fit(
                ["large", "mid", "small"]
            ).transform(["mid"])[0]

            x_input = np.array([[
                *[slider_values[f] for f in list(TOOLTIPS.keys())],
                sector_enc, size_enc
            ]])

            sv, pred_class, explain_method = explain_instance(
                xgb_model, x_input, FEATURE_COLS
            )
            if explain_method == "xgb_contrib":
                st.caption(
                    "Using XGBoost native feature contributions (SHAP TreeExplainer "
                    "failed on this runtime — often due to XGBoost/sklearn version mismatch)."
                )

            # Build Plotly waterfall from SHAP values
            feat_names    = [f.replace("_", " ").title() for f in FEATURE_COLS]
            shap_series   = pd.Series(sv, index=feat_names).sort_values(key=abs, ascending=False).head(10)
            measure       = ["relative"] * len(shap_series) + ["total"]
            x_vals        = list(shap_series.values) + [sum(shap_series.values)]
            y_labels      = list(shap_series.index) + ["Total SHAP"]
            bar_colours   = ["#059669" if v >= 0 else "#DC2626" for v in x_vals]

            fig_shap = go.Figure(go.Waterfall(
                orientation="h",
                measure=measure,
                x=x_vals,
                y=y_labels,
                connector=dict(line=dict(color="#D1D5DB", width=1)),
                increasing=dict(marker=dict(color="#059669")),
                decreasing=dict(marker=dict(color="#DC2626")),
                totals=dict(marker=dict(color="#1B3A6B")),
                textposition="outside",
                text=[f"{v:+.3f}" for v in x_vals],
                textfont=dict(size=9),
            ))
            fig_shap.update_layout(
                title=dict(
                    text=f"Top 10 Feature Contributions<br>"
                         f"<sup>Predicted tier: {['Nascent','Developing','Established','Leading'][pred_class]}</sup>",
                    font=dict(size=12, color="#1B3A6B")
                ),
                height=400,
                margin=dict(t=60, b=20, l=160, r=60),
                xaxis_title="SHAP Value",
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_shap, use_container_width=True)
            st.caption(
                "Green bars push toward higher tier · Red bars push toward lower tier"
            )
        except Exception as e:
            st.warning(f"SHAP chart unavailable: {e}")

st.markdown(
    "<div style='text-align:center;font-size:0.75rem;color:#9CA3AF;margin-top:20px;'>"
    "AIRI v1.0 . UK Debt Management AI Readiness"
    "</div>",
    unsafe_allow_html=True,
)