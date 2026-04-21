# app/pages/5_About.py
# AIRI Page 5 — About / Methodology
# Framework overview | Dimension definitions | Regulatory context |
# Config display


import sys
from pathlib import Path
import pandas as pd
import streamlit as st
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.airi_engine import AIRIConfig

@st.cache_resource
def load_config():
    return AIRIConfig(str(PROJECT_ROOT / "airi_config.yaml"))

TIER_COLOURS = {
    "nascent": "#DC2626","developing": "#D97706",
    "established": "#059669","leading": "#1B3A6B",
}

# Page header 
st.markdown(
    "<h1 style='color:#1B3A6B;'> About & Methodology</h1>"
    "<p style='color:#6B7280;'>Framework design, dimension definitions, "
    "regulatory context, and live configuration.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

config = load_config()
dims   = config.get_dimensions()
tiers  = config.get_tiers()

# Framework overview 
st.markdown("### What is AIRI?")
st.markdown("""
**AIRI (AI Readiness Index)** is a quantitative, configurable, and explainable scoring system
that assesses whether a UK debt management institution is genuinely ready to deploy AI responsibly —
ethically, technically, and in regulatory compliance.

Given structured input data about an institution's capabilities, AIRI produces:
- A **composite AIRI score** (0-100) representing overall AI readiness
- **Dimension-level subscores** showing strengths and gaps across 5 domains
- A **readiness tier** classification: Nascent / Developing / Established / Leading
- **SHAP-based explanations** of what drives each institution's specific score
- **Prioritised recommendations** ordered by gap severity
""")

# Scoring algorithm 
st.markdown("---")
st.markdown("## Scoring Algorithm")
st.markdown("""
The AIRI scoring engine applies a **three-step deterministic algorithm**:

**Step 1 — Normalise raw indicators (1-5 → 0-1)**
```
normalised = (raw_score - likert_min) / (likert_max − likert_min)
```

**Step 2 — Compute dimension score (0–100)**
```
dimension_score = Σ (normalised_indicator × indicator_weight) × 100
```

**Step 3 — Compute composite AIRI score (0–100)**
```
airi_score = Σ (dimension_score x dimension_weight)
```
All weights are loaded from `airi_config.yaml` — no weight is hardcoded in Python.
""")

# Readiness tiers 
st.markdown("---")
st.markdown("##  Readiness Tiers")
tier_info = {
    "nascent": ("0 – 39",  "Critical readiness gaps",        "Foundation-first remediation"),
    "developing": ("40 – 59", "Partial readiness",          "Targeted gap-filling"),
    "established": ("60 – 79", "Solid foundation for AI",     "Optimisation and monitoring"),
    "leading": ("80 – 100","Best-in-class readiness",        "Innovation and knowledge sharing"),
}
cols = st.columns(4)
for col, (tier, (score_range, interp, action)) in zip(cols, tier_info.items()):
    col.markdown(
        f"<div style='background:{TIER_COLOURS[tier]};color:white;"
        f"border-radius:10px;padding:16px;text-align:center;'>"
        f"<div style='font-size:1.1rem;font-weight:700;'>{tier.capitalize()}</div>"
        f"<div style='font-size:0.85rem;margin:4px 0;'>{score_range}</div>"
        f"<div style='font-size:0.78rem;opacity:0.9;'>{interp}</div>"
        f"<div style='font-size:0.75rem;opacity:0.8;margin-top:6px;"
        f"font-style:italic;'>{action}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

# Dimension definitions 
st.markdown("---")
st.markdown("##  Five AIRI Dimensions")

dim_descriptions = {
    "data_infrastructure": (
        "Data Infrastructure (20%)",
        "Measures the quality, governance, and integration capability of the institution's "
        "data assets — the foundational layer all AI systems depend on.",
        ["data_quality","data_governance","data_integration"],
    ),
    "technological_maturity": (
        "Technological Maturity (20%)",
        "Assesses the institution's AI/ML tooling, infrastructure resilience, and "
        "system capability to support AI deployment at scale.",
        ["system_capability","ai_tooling","infrastructure_resilience"],
    ),
    "regulatory_compliance": (
        "Regulatory Compliance (25%)",
        "The highest-weighted dimension. Measures alignment with FCA guidance, "
        "Consumer Duty obligations, and audit capability.",
        ["fca_alignment","consumer_duty","audit_trail"],
    ),
    "organisational_capability": (
        "Organisational Capability (20%)",
        "Evaluates people, culture, and change management — often the weakest link "
        "in AI adoption regardless of technical strength.",
        ["talent_readiness","change_management","leadership_commitment"],
    ),
    "ethical_governance": (
        "Ethical Governance (15%)",
        "Measures the maturity of ethical AI controls including bias detection, "
        "model explainability, and accountability structures.",
        ["bias_mitigation","explainability","accountability_structures"],
    ),
}

for dim_key, (title, desc, indicators) in dim_descriptions.items():
    with st.expander(f"**{title}**"):
        st.markdown(desc)
        dim_data = dims[dim_key]
        rows = []
        for ind, weight in dim_data["indicators"].items():
            rows.append({
                "Indicator": ind.replace("_"," ").title(),
                "Weight": f"{weight*100:.0f}%",
            })
        st.table(pd.DataFrame(rows))

# Regulatory context 
st.markdown("---")
st.markdown("## Regulatory Context")
st.markdown("""
AIRI is designed for the specific regulatory environment facing UK debt management institutions:

**FCA Discussion Paper DP5/22 — AI and Machine Learning**
The FCA's guidance sets out expectations for governance, transparency, and accountability
in AI systems. AIRI's Regulatory Compliance dimension (25% weight) directly maps to these
principles. An `fca_alignment` score of 5 indicates full documented compliance.

**Consumer Duty (FCA PS22/9)**
Effective from July 2023, Consumer Duty requires firms to demonstrate good outcomes for retail
customers. AIRI's `consumer_duty` indicator assesses whether AI touchpoints have been audited
against Consumer Duty obligations and whether outcomes monitoring is in place.

**Audit Trail Requirements**
Both FCA DP5/22 and Consumer Duty imply that firms must be able to explain and audit
AI-influenced decisions. AIRI's `audit_trail` indicator measures this capability
from manual logs (score 3) to automated immutable trails with retrieval SLAs (score 5).
""")

# Live config display 
st.markdown("---")
st.markdown("##  Live Configuration (airi_config.yaml)")
st.caption("All weights are loaded from this file at runtime. No weights are hardcoded.")

config_rows = []
for dim_name, dim_data in dims.items():
    config_rows.append({
        "Dimension": dim_name.replace("_"," ").title(),
        "Dim Weight": f"{dim_data['weight']*100:.0f}%",
        "Indicator": "",
        "Ind Weight": "",
    })
    for ind, w in dim_data["indicators"].items():
        config_rows.append({
            "Dimension": "",
            "Dim Weight": "",
            "Indicator": ind.replace("_"," ").title(),
            "Ind Weight": f"{w*100:.0f}%",
        })

st.dataframe(pd.DataFrame(config_rows), use_container_width=True, height=420)

# Weight validation
dim_sum = sum(d["weight"] for d in dims.values())
st.success(f"✓ Dimension weight sum: {dim_sum:.3f} (valid)")

# System info 
st.markdown("---")
st.markdown("##  System Information")
c1, c2 = st.columns(2)
c1.markdown(f"""
| Component | Detail |
|---|---|
| Scoring engine | `src/airi_engine.py` |
| Configuration  | `airi_config.yaml` |
| Dataset        | 150 synthetic institutions |
| Random seed    | 42 (all components) |
| ML model       | XGBoost 1.7.x |
| Explainability | SHAP TreeExplainer |
""")
c2.markdown(f"""
| Component | Detail |
|---|---|
| Python | 3.8.10 |
| Streamlit | 1.22.x |
| Charts | Plotly (all pages) |
| Offline | ✓ No external APIs |
| Config-driven | ✓ Weights in YAML |
| CVI validated | Pending expert survey |
""")

st.markdown(
    "<div style='text-align:center;font-size:0.75rem;color:#9CA3AF;margin-top:20px;'>"
    "AIRI v1.0 . UK Debt Management AI Readiness"
    "</div>",
    unsafe_allow_html=True,
)