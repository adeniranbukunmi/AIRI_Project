import yaml
import pandas as pd
import numpy as np
from pathlib import Path



class AIRIConfig:
    """Loads and validates airi_config.yaml."""
 
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path.resolve()}\n"
            )
        with open(self.config_path, "r") as f:
            self._raw = yaml.safe_load(f)
 
        self.scoring    = self._raw["scoring"]
        self.dimensions = self._raw["dimensions"]
        self.tiers      = self._raw["tiers"]
        self.validate()
 
    def validate(self) -> None:
        """Validates all weight rules. Raises ValueError on any failure."""
        errors = []
 
        # Rule 1: dimension weights must sum to 1.0 (±0.001)
        dim_total = sum(v["weight"] for v in self.dimensions.values())
        if abs(dim_total - 1.0) > 0.001:
            errors.append(
                f"Dimension weights sum to {dim_total:.4f}, must be 1.0."
            )
 
        # Rule 2: indicator weights within each dimension must sum to 1.0
        for dim_name, dim_data in self.dimensions.items():
            ind_total = sum(dim_data["indicators"].values())
            if abs(ind_total - 1.0) > 0.001:
                errors.append(
                    f"Indicator weights in '{dim_name}' sum to {ind_total:.4f}, must be 1.0."
                )
 
        # Rule 3: required scoring keys must exist
        for key in ["scale_min", "scale_max", "likert_min", "likert_max"]:
            if key not in self.scoring:
                errors.append(f"Missing scoring key: '{key}'.")
 
        if errors:
            raise ValueError(
                "airi_config.yaml validation failed:\n" +
                "\n".join(f"  * {e}" for e in errors)
            )
 
    def get_dimensions(self) -> dict:
        return self.dimensions
 
    def get_tiers(self) -> dict:
        return self.tiers
 
    def get_scoring_params(self) -> dict:
        return self.scoring
 
    def __repr__(self):
        return (
            f"AIRIConfig(path='{self.config_path}', "
            f"dimensions={list(self.dimensions.keys())}, "
            f"tiers={list(self.tiers.keys())})"
        )

class AIRIScorer:
    """Applies the 3-step AIRI scoring algorithm to institutional profiles."""
 
    def __init__(self, config: AIRIConfig):
        self.config       = config
        self.dims         = config.get_dimensions()
        self.params       = config.get_scoring_params()
        self.likert_min   = self.params["likert_min"]
        self.likert_max   = self.params["likert_max"]
        self.likert_range = self.likert_max - self.likert_min  # = 4
 
    def _normalise(self, raw_score: float) -> float:
        """Step 1: (raw - likert_min) / (likert_max - likert_min)"""
        return (raw_score - self.likert_min) / self.likert_range
 
    def _validate_row(self, row: pd.Series) -> None:
        errors = []
        for dim_data in self.dims.values():
            for ind_name in dim_data["indicators"]:
                if ind_name not in row.index:
                    errors.append(f"Missing column: '{ind_name}'")
                    continue
                val = row[ind_name]
                if not isinstance(val, (int, np.integer)):
                    errors.append(f"'{ind_name}' = {val} is not an integer.")
                elif not (self.likert_min <= val <= self.likert_max):
                    errors.append(f"'{ind_name}' = {val} out of range [{self.likert_min},{self.likert_max}].")
        if errors:
            raise ValueError(
                f"Row validation failed for '{row.get('institution_id', 'unknown')}':\n" +
                "\n".join(f"  * {e}" for e in errors)
            )
 
    def score_institution(self, row: pd.Series) -> dict:
        """Score a single institution. Returns score_d1-5, airi_score, readiness_tier."""
        self._validate_row(row)
        scores     = {}
        airi_score = 0.0
 
        for i, (dim_name, dim_data) in enumerate(self.dims.items(), start=1):
            dim_weight = dim_data["weight"]
            indicators = dim_data["indicators"]
 
            # Step 2: dimension score (0-100)
            dim_score = sum(
                self._normalise(row[ind_name]) * ind_weight
                for ind_name, ind_weight in indicators.items()
            ) * 100
 
            scores[f"score_d{i}"] = round(dim_score, 4)
            # Step 3: accumulate composite
            airi_score += dim_score * dim_weight
 
        scores["airi_score"]     = round(airi_score, 4)
        scores["readiness_tier"] = self.assign_tier(airi_score)
        return scores
 
    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score all rows. Appends score columns and returns full DataFrame."""
        score_records = df.apply(self.score_institution, axis=1)
        score_df      = pd.DataFrame(list(score_records))
        return pd.concat([df.reset_index(drop=True), score_df], axis=1)

    
    def assign_tier(self, airi_score: float) -> str:
        """Map float score to tier string using config thresholds.
 
        Uses low <= score < high for all tiers except leading (last),
        which uses <= to capture score=100. This ensures boundary scores
        like 40, 60, 80 resolve to the higher tier as the spec intends.
        """
        tiers = list(self.config.get_tiers().items())
        for i, (tier_name, bounds) in enumerate(tiers):
            low, high = bounds
            is_last = (i == len(tiers) - 1)
            if is_last:
                if low <= airi_score <= high:
                    return tier_name
            else:
                if low <= airi_score < high:
                    return tier_name
        return "nascent" if airi_score < 0 else "leading"
 
    
_LIBRARY = {
 
        "data_infrastructure": [
            {
                "action": "Implement automated real-time data quality monitoring with SLAs.",
                "rationale": "Without reliable data quality controls, AI models trained on "
                            "your data will produce unreliable outputs, undermining FCA "
                            "confidence and Consumer Duty compliance.",
                "applies_when": lambda s: s < 50,
            },
            {
                "action": "Establish a formal data governance framework with named data "
                        "stewards, lineage tracking, and audit trails.",
                "rationale": "Data governance is the single highest-weighted indicator in "
                            "this dimension (35%). Formalising ownership and traceability "
                            "directly accelerates readiness in Dimensions 3 and 5.",
                "applies_when": lambda s: s < 70,
            },
            {
                "action": "Build a unified data platform with real-time API integrations "
                        "across all operational systems.",
                "rationale": "Siloed data prevents AI agents from accessing the breadth of "
                            "signals needed for accurate credit risk and arrears management. "
                            "Integration is a prerequisite for production AI deployment.",
                "applies_when": lambda s: s < 85,
            },
            {
                "action": "Conduct a full data asset inventory and classify datasets by "
                        "sensitivity, completeness, and AI-readiness.",
                "rationale": "Knowing what data you have — and its quality — is the "
                            "foundation step before any governance or integration work can "
                            "be prioritised effectively.",
                "applies_when": lambda s: s < 40,
            },
        ],
    
        "technological_maturity": [
            {
                "action": "Deploy a production ML platform with CI/CD pipelines, a model "
                        "registry, and automated monitoring.",
                "rationale": "Ad hoc experimentation does not scale to production AI. A "
                            "formal MLOps platform reduces deployment risk and enables the "
                            "audit trail regulators expect.",
                "applies_when": lambda s: s < 60,
            },
            {
                "action": "Implement automated model retraining and drift detection across "
                        "all deployed AI systems.",
                "rationale": "Models degrade silently as data distributions shift. Without "
                            "drift detection, an institution cannot demonstrate ongoing "
                            "model fitness — a core FCA expectation.",
                "applies_when": lambda s: s < 75,
            },
            {
                "action": "Develop and test a resilience framework covering AI workloads "
                        "with documented RTO and RPO targets.",
                "rationale": "AI system failures in debt management can directly harm "
                            "customers. A tested resilience framework demonstrates "
                            "operational maturity to both regulators and auditors.",
                "applies_when": lambda s: s < 85,
            },
            {
                "action": "Pilot at least one AI use case end-to-end in a sandboxed "
                        "environment to establish baseline ML infrastructure.",
                "rationale": "Institutions with no ML infrastructure (score 1–2) need a "
                            "concrete pilot to identify gaps before investing in "
                            "enterprise-scale tooling.",
                "applies_when": lambda s: s < 35,
            },
        ],
    
        "regulatory_compliance": [
            {
                "action": "Complete a documented alignment review against FCA DP5/22 AI "
                        "guidance and publish an internal compliance statement.",
                "rationale": "FCA alignment is the highest-weighted indicator in this "
                            "dimension (40%). Documented alignment is a direct mitigant "
                            "against regulatory censure and a prerequisite for AI "
                            "deployment approval.",
                "applies_when": lambda s: s < 60,
            },
            {
                "action": "Map all AI touchpoints to Consumer Duty obligations and implement "
                        "outcomes monitoring for each.",
                "rationale": "Consumer Duty requires firms to demonstrate good outcomes for "
                            "customers. Unmapped AI touchpoints create blind spots that "
                            "expose the institution to enforcement action.",
                "applies_when": lambda s: s < 70,
            },
            {
                "action": "Deploy an automated, immutable audit trail for all AI-influenced "
                        "decisions with a retrieval SLA.",
                "rationale": "Manual audit logs are insufficient at scale. An automated "
                            "trail enables rapid response to FCA information requests and "
                            "supports customer right-to-explanation obligations.",
                "applies_when": lambda s: s < 80,
            },
            {
                "action": "Assign a dedicated regulatory AI compliance owner and schedule "
                        "quarterly FCA guidance reviews.",
                "rationale": "The FCA AI regulatory landscape is evolving rapidly. Without "
                            "a named owner tracking developments, compliance gaps accumulate "
                            "unnoticed until audit.",
                "applies_when": lambda s: s < 50,
            },
        ],
    
        "organisational_capability": [
            {
                "action": "Launch an organisation-wide AI literacy programme and create "
                        "dedicated AI governance roles.",
                "rationale": "AI literacy gaps are the most common cause of failed AI "
                            "adoption regardless of technical investment. Broad literacy "
                            "accelerates change absorption and reduces resistance.",
                "applies_when": lambda s: s < 55,
            },
            {
                "action": "Implement a formal AI change management framework with structured "
                        "stakeholder engagement at each deployment stage.",
                "rationale": "Ad hoc change processes create inconsistent adoption. A "
                            "formal framework ensures staff, customers, and regulators are "
                            "engaged appropriately at every AI deployment milestone.",
                "applies_when": lambda s: s < 70,
            },
            {
                "action": "Secure board-level ownership of the AI strategy with a dedicated "
                        "investment budget and KPIs tracked at executive level.",
                "rationale": "Leadership commitment (30% weight) is the multiplier for all "
                            "other capability investments. Without board sponsorship, "
                            "AI initiatives stall at proof-of-concept stage.",
                "applies_when": lambda s: s < 80,
            },
            {
                "action": "Identify and develop at least two internal AI champions to bridge "
                        "technical and business teams.",
                "rationale": "Institutions with no internal AI skills (score 1–2) cannot "
                            "effectively manage vendor relationships or evaluate AI outputs "
                            "critically. Internal champions are the minimum viable "
                            "capability foundation.",
                "applies_when": lambda s: s < 35,
            },
        ],
    
        "ethical_governance": [
            {
                "action": "Implement a systematic bias testing framework covering pre- and "
                        "post-deployment stages with documented remediation procedures.",
                "rationale": "Undetected bias in credit risk or vulnerability identification "
                            "AI creates direct Consumer Duty violations and potential "
                            "discrimination liability. Systematic testing is non-negotiable "
                            "for customer-facing AI.",
                "applies_when": lambda s: s < 60,
            },
            {
                "action": "Apply SHAP or LIME explainability methods to all customer-facing "
                        "AI models and log explanations per decision.",
                "rationale": "Unexplainable AI decisions cannot be defended to regulators "
                            "or challenged by customers. Logged SHAP explanations directly "
                            "satisfy FCA expectations for transparent AI.",
                "applies_when": lambda s: s < 75,
            },
            {
                "action": "Document an accountability framework naming an AI owner per "
                        "system with clear escalation paths.",
                "rationale": "Informal accountability creates gaps when AI systems fail. "
                            "A documented framework ensures rapid incident response and "
                            "clear regulatory reporting lines.",
                "applies_when": lambda s: s < 85,
            },
            {
                "action": "Conduct an ethics impact assessment for each deployed or planned "
                        "AI use case before go-live.",
                "rationale": "Institutions with no formal ethical AI controls (score 1–2) "
                            "need a structured assessment process as the minimum entry "
                            "point before any bias or explainability tooling is deployed.",
                "applies_when": lambda s: s < 35,
            },
        ],
    }
        
 
# ──────────────────────────────────────────────────────────────────────
# CLASS 3: AIRIRecommender  (full implementation — Step 4)
# ──────────────────────────────────────────────────────────────────────
 
class AIRIRecommender:
    """Generates prioritised recommendations based on dimension gap scores.
 
    Gap score = 100 - dimension_score.
    Recommendations are sorted by gap_score descending (highest gap first).
 
    Usage:
        recommender = AIRIRecommender(config)
        recs = recommender.recommend(scored_row)
        # recs[0] is the highest-priority recommendation
 
    Each recommendation dict contains:
        {dimension, gap_score, priority_rank, action, rationale}
    """
 
    # Maps dimension name → score column in scored DataFrame
    _DIM_SCORE_COLS = {
        "data_infrastructure":     "score_d1",
        "technological_maturity":  "score_d2",
        "regulatory_compliance":   "score_d3",
        "organisational_capability": "score_d4",
        "ethical_governance":      "score_d5",
    }
 
    # Human-readable labels for display
    _DIM_LABELS = {
        "data_infrastructure":       "Data Infrastructure",
        "technological_maturity":    "Technological Maturity",
        "regulatory_compliance":     "Regulatory Compliance",
        "organisational_capability": "Organisational Capability",
        "ethical_governance":        "Ethical Governance",
    }
 
    def __init__(self, config: AIRIConfig):
        self.config = config
 
    def recommend(self, scored_row: pd.Series) -> list:
        """Generate prioritised recommendations for a scored institution row.
 
        Args:
            scored_row: A pd.Series that includes score_d1 through score_d5
                        (i.e. a row already processed by AIRIScorer).
 
        Returns:
            List of dicts sorted by gap_score descending:
            [
              {
                "dimension":      str,   # dimension name (human-readable)
                "gap_score":      float, # 100 - dimension_score
                "priority_rank":  int,   # 1 = highest priority
                "action":         str,   # specific recommended action
                "rationale":      str,   # why this matters for this institution
              },
              ...
            ]
        """
        # Validate required score columns are present
        missing = [
            col for col in self._DIM_SCORE_COLS.values()
            if col not in scored_row.index
        ]
        if missing:
            raise ValueError(
                f"scored_row is missing columns: {missing}. "
                "Run AIRIScorer.score_institution() before calling recommend()."
            )
 
        raw_recs = []
 
        for dim_key, score_col in self._DIM_SCORE_COLS.items():
            dim_score = float(scored_row[score_col])
            gap_score = round(100.0 - dim_score, 4)
            lib_entries = _LIBRARY.get(dim_key, [])
 
            # Select all library entries whose applies_when condition is met
            triggered = [
                e for e in lib_entries if e["applies_when"](dim_score)
            ]
 
            # Fallback: if no conditions triggered (very high scorer),
            # always include the last entry as a best-practice nudge
            if not triggered:
                triggered = [lib_entries[-1]]
 
            for entry in triggered:
                raw_recs.append({
                    "dimension":   self._DIM_LABELS[dim_key],
                    "gap_score":   gap_score,
                    "priority_rank": None,   # assigned after sorting
                    "action":      entry["action"],
                    "rationale":   entry["rationale"],
                })
 
        # Sort by gap_score descending (highest gap = highest priority)
        raw_recs.sort(key=lambda x: x["gap_score"], reverse=True)
 
        # Assign priority ranks
        for rank, rec in enumerate(raw_recs, start=1):
            rec["priority_rank"] = rank
 
        return raw_recs
 
    def top_n(self, scored_row: pd.Series, n: int = 3) -> list:
        """Convenience method: return only the top-n recommendations.
 
        Used by Streamlit Page 1 which displays top 3 priority actions.
        """
        return self.recommend(scored_row)[:n]