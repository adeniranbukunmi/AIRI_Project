# AIRI — AI Readiness Index for UK Debt Management Institutions

## Environment Setup (Step 1)

### 1. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 2. Install all dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify installation
```bash
python -c 'import xgboost, shap, streamlit'
```
No output = success.

### 4. Run the Streamlit app (after Step 8 — ML pipeline complete)
```bash
streamlit run app/streamlit_app.py
```

---

## Project Structure
```
airi-project/
├── airi_config.yaml          # Master config: weights + tier thresholds
├── requirements.txt          # Pinned Python dependencies
├── README.md
├── data/                     # CSV inputs and outputs
├── src/                      # Core Python modules
│   ├── __init__.py
│   ├── airi_engine.py        # AIRIConfig + AIRIScorer + AIRIRecommender
│   ├── data_generator.py     # Synthetic dataset generator
│   └── ml_pipeline.py        # ML training (mirrors notebook 03)
├── notebooks/                # Jupyter development notebooks
├── models/                   # Serialised model artefacts (.pkl)
├── app/                      # Streamlit application
│   ├── streamlit_app.py
│   └── pages/
├── powerbi/                  # Power BI report file
├── survey/                   # Expert validation survey
└── outputs/                  # Exported charts and reports
    ├── charts/
    └── reports/
```

## Build Order
Follow `Section 10` of the Master Specification (16 steps).  
**Do not skip ahead** — each step depends on the previous one's output file.



An end-to-end scoring engine and analytical framework designed to assess the AI readiness of UK debt management institutions across five dimensions: Data Infrastructure, Technological Maturity, Regulatory Compliance, Organisational Capability, and Ethical Governance.

##  Project Overview
This project fulfills the technical requirements for the MSc Information Technology dissertation. It features:
* **Scoring Engine:** A weighted Likert-scale algorithm for institutional assessment.
* **ML Pipeline:** XGBoost-based classification with SHAP explainability.
* **Streamlit App:** An interactive prototype for real-time scoring.
* **Power BI Dashboard:** Stakeholder-level visual analytics.

##  Tech Stack
* **Language:** Python 3.11
* **Logic:** Pandas, NumPy, PyYAML
* **ML:** XGBoost, Scikit-Learn, SHAP
* **UI:** Streamlit, Plotly
* **BI:** Power BI Desktop

## Installation & Usage
1. Clone the repo: `git clone <your-repo-url>`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the pipeline: Execute notebooks in `notebooks/` sequentially.
4. Launch the app: `streamlit run app/streamlit_app.py`
