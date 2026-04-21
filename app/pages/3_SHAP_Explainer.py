
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import shap
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.airi_engine import AIRIConfig, AIRIScorer

TIER_COLOURS = {
    "nascent": "#DC2626", "developing": "#D97706",
    "established": "#059669", "leading": "#1B3A6B",
}
INDICATOR_COLS = [
    "data_quality","data_governance","data_integration",
    "system_capability","ai_tooling","infrastructure_resilience",
    "fca_alignment","consumer_duty","audit_trail",
    "talent_readiness","change_management","leadership_commitment",
    "bias_mitigation","explainability","accountability_structures",
]
FEATURE_COLS = INDICATOR_COLS + ["sector_enc","size_enc"]
TIER_MAP     = {"nascent":0,"developing":1,"established":2,"leading":3}
TIER_NAMES   = ["Nascent","Developing","Established","Leading"]

@st.cache_resource
def load_config():
    return AIRIConfig(str(PROJECT_ROOT / "airi_config.yaml"))

@st.cache_resource
def load_xgb():
    model_path = PROJECT_ROOT / "models" / "xgb_model.pkl"
    if not model_path.exists():
        st.error(f"Model file not found at {model_path}")
    return joblib.load(model_path)

@st.cache_data
def load_cohort():
    return pd.read_csv(PROJECT_ROOT / "data" / "scored_institutions.csv")

@st.cache_data
def load_shap():
    return pd.read_csv(PROJECT_ROOT / "data" / "shap_values.csv")

# ── Page header ───────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#1B3A6B;'>SHAP Explainer</h1>"
    "<p style='color:#6B7280;'>Select any institution to understand "
    "which indicators drove their AIRI score.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

df      = load_cohort()
shap_df = load_shap()

try:
    xgb_model = load_xgb()
    model_ok  = True
except Exception:
    model_ok  = False

#  Institution selector 
df["display"] = df["institution_id"] + " — " + df["institution_name"] + \
                " (" + df["readiness_tier"].str.capitalize() + \
                ", " + df["airi_score"].round(1).astype(str) + ")"
selected = st.selectbox("Select institution:", df["display"].tolist())
inst_id  = selected.split(" — ")[0]
row      = df[df["institution_id"] == inst_id].iloc[0]

# Institution header 
tier        = row["readiness_tier"]
tier_colour = TIER_COLOURS[tier]

c1, c2, c3, c4 = st.columns(4)
c1.metric("AIRI Score",    f"{row['airi_score']:.1f}")
c2.metric("Sector",        row["sector"].replace("_"," ").title())
c3.metric("Size",          row["institution_size"].capitalize())
c4.markdown(
    f"<div style='background:{tier_colour};color:white;border-radius:20px;"
    f"padding:10px;text-align:center;font-weight:700;margin-top:8px;'>"
    f"{tier.upper()}</div>",
    unsafe_allow_html=True,
)
st.markdown("---")

# SHAP waterfall 
left, right = st.columns([1.2, 1], gap="large")

with left:
    st.markdown("#### SHAP Waterfall Chart")

    if model_ok:
        try:
            from sklearn.preprocessing import LabelEncoder
            # Encode categorical variables
            le_s = LabelEncoder().fit(["credit_union","debt_purchaser", "fintech_lender","retail_bank"])
            le_z = LabelEncoder().fit(["large","mid","small"])
            s_enc = int(le_s.transform([row["sector"]])[0])
            z_enc = int(le_z.transform([row["institution_size"]])[0])

            # 1. Force data into a clean 2D array (1 row, N columns)
            features = [float(row[f]) for f in INDICATOR_COLS] + [float(s_enc), float(z_enc)]
            x_in = np.array(features).reshape(1, -1)
            
            # 2. Compute SHAP values
            explainer = shap.TreeExplainer(xgb_model)
            shap_vals = explainer.shap_values(x_in)
            pred_cls  = int(xgb_model.predict(x_in)[0])

            # 3. Handle different SHAP output formats (List vs Array)
            if isinstance(shap_vals, list):
                # Multi-class output: pick values for the predicted class
                sv = shap_vals[pred_cls]
            else:
                # Single-class output
                sv = shap_vals

            # 4. CRITICAL FIX: Force sv to be 1D to prevent the "ndarray" error
            sv = np.array(sv).flatten()

            # 5. Create the Series for the chart
            feat_labels = [f.replace("_"," ").title() for f in FEATURE_COLS]
            shap_series = pd.Series(sv, index=feat_labels)\
                            .sort_values(key=abs, ascending=False).head(12)

            measure = ["relative"] * len(shap_series) + ["total"]
            x_vals  = list(shap_series.values) + [float(sum(shap_series.values))]
            y_lbls  = list(shap_series.index)  + ["Total SHAP"]

            # 6. Build the Waterfall Chart
            fig_wf = go.Figure(go.Waterfall(
                orientation="h", measure=measure,
                x=x_vals, y=y_lbls,
                connector=dict(line=dict(color="#D1D5DB",width=1)),
                increasing=dict(marker=dict(color="#059669")),
                decreasing=dict(marker=dict(color="#DC2626")),
                totals=dict(marker=dict(color="#1B3A6B")),
                text=[f"{v:+.3f}" for v in x_vals],
                textposition="outside",
                textfont=dict(size=9, color="black"), # Ensure text is black
            ))
            
            fig_wf.update_layout(
                title=f"Predicted tier: {TIER_NAMES[pred_cls]}",
                title_font=dict(color="black"),
                height=420,
                margin=dict(t=40,b=20,l=160,r=80),
                xaxis=dict(title="SHAP Value", title_font=dict(color="black"), tickfont=dict(color="black")),
                yaxis=dict(tickfont=dict(color="black")),
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            
            st.plotly_chart(fig_wf, use_container_width=True)
            st.caption("Green = pushes toward higher tier  ·   Red = pushes toward lower tier")
        except Exception:
            st.info(" Select an institution from the list above to view the SHAP analysis.")
    else:
        st.info("Run Notebook 03 to generate models/xgb_model.pkl")

# Feature contribution table 
with right:
    st.markdown("#### Feature Contribution Table")

    # Use pre-computed shap_values.csv if institution is in test set
    if inst_id in shap_df["institution_id"].values:
        shap_row = shap_df[shap_df["institution_id"] == inst_id].iloc[0]
        contrib  = pd.DataFrame({
            "Feature":      [f.replace("_"," ").title() for f in FEATURE_COLS
                             if f in shap_row.index],
            "Raw Score":    [int(row[f]) if f in row.index else "—"
                             for f in FEATURE_COLS if f in shap_row.index],
            "SHAP |Value|": [round(abs(shap_row[f]),4)
                             for f in FEATURE_COLS if f in shap_row.index],
        }).sort_values("SHAP |Value|", ascending=False).reset_index(drop=True)
        st.dataframe(contrib, use_container_width=True, height=380)
    else:
        # Show raw indicator scores as fallback
        ind_data = pd.DataFrame({
            "Indicator": [f.replace("_"," ").title() for f in INDICATOR_COLS],
            "Score (1-5)": [int(row[f]) for f in INDICATOR_COLS],
        })
        st.dataframe(ind_data, use_container_width=True, height=380)
        st.caption("Full SHAP values available for test-set institutions only.")

# Plain-English narrative 
st.markdown("---")
st.markdown("#### Plain-English Narrative")

dim_names = ["Data Infrastructure","Technological Maturity",
             "Regulatory Compliance","Organisational Capability","Ethical Governance"]
dim_scores = [row["score_d1"],row["score_d2"],row["score_d3"],
              row["score_d4"],row["score_d5"]]
strongest = dim_names[int(np.argmax(dim_scores))]
weakest   = dim_names[int(np.argmin(dim_scores))]
gap       = round(100 - row["airi_score"], 1)

tier_interp = {
    "nascent":     "has critical readiness gaps and requires immediate foundation-level remediation",
    "developing":  "shows partial readiness with targeted improvement areas",
    "established": "has a solid foundation for responsible AI deployment",
    "leading":     "demonstrates best-in-class AI readiness across all dimensions",
}

narrative = (
    f"**{row['institution_name']}** is a **{row['institution_size']} "
    f"{row['sector'].replace('_',' ')}** with an AIRI score of "
    f"**{row['airi_score']:.1f}/100**, placing it in the "
    f"**{tier.capitalize()}** tier. "
    f"This institution {tier_interp[tier]}. "
    f"Its strongest dimension is **{strongest}** "
    f"(score: {max(dim_scores):.1f}) and its weakest is **{weakest}** "
    f"(score: {min(dim_scores):.1f}). "
    f"Closing the gap to a score of 100 requires an improvement of **{gap:.1f} points** "
    f"across the five AIRI dimensions. "
    f"Priority action should focus on **{weakest}**, where the largest "
    f"readiness gap exists relative to the leading-practice benchmark."
)
st.info(narrative)

st.markdown(
    "<div style='text-align:center;font-size:0.75rem;color:#9CA3AF;margin-top:20px;'>"
    "AIRI v1.0 . UK Debt Management AI Readiness"
    "</div>",
    unsafe_allow_html=True,
)