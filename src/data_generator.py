import random
import numpy as np
import pandas as pd
from pathlib import Path
from faker import Faker
 
# ── Global seed ───────────────────────────────────────────────────────
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
fake = Faker("en_GB")
fake.seed_instance(RANDOM_SEED)
 
# ── Indicator columns — order matches spec Section 4.3 ───────────────
INDICATORS = [
    "data_quality", "data_governance", "data_integration",          # D1
    "system_capability", "ai_tooling", "infrastructure_resilience", # D2
    "fca_alignment", "consumer_duty", "audit_trail",                # D3
    "talent_readiness", "change_management", "leadership_commitment", # D4
    "bias_mitigation", "explainability", "accountability_structures", # D5
]
 
# ── Sector config — absolute per-indicator base means ─────────────────
# Retail banks: highest D3 regulatory compliance
# Fintech:      highest D2 technological maturity
# Debt purchasers: average across board
# Credit unions:  lowest overall maturity
SECTOR_CONFIG = {
    "retail_bank": {
        "n": 45,
        "mean_base": np.array([
            3.6, 3.8, 3.5,   # D1: strong data governance
            3.4, 3.3, 3.5,   # D2: moderate tech
            4.1, 4.0, 3.9,   # D3: highest regulatory compliance
            3.6, 3.6, 3.8,   # D4: leadership driven
            3.5, 3.3, 3.6,   # D5: moderate ethics
        ]),
    },
    "debt_purchaser": {
        "n": 37,
        "mean_base": np.array([
            2.9, 3.0, 2.8,   # D1: average data
            2.7, 2.8, 2.7,   # D2: basic tech
            3.2, 3.2, 3.1,   # D3: growing compliance
            2.8, 2.9, 2.9,   # D4: moderate capability
            2.8, 2.7, 2.8,   # D5: basic ethics
        ]),
    },
    "fintech_lender": {
        "n": 38,
        "mean_base": np.array([
            3.4, 3.3, 3.7,   # D1: strong integration
            3.8, 3.9, 3.6,   # D2: highest tech maturity
            3.4, 3.4, 3.3,   # D3: moderate compliance
            3.6, 3.5, 3.5,   # D4: talent strong
            3.6, 3.7, 3.5,   # D5: explainability focus
        ]),
    },
    "credit_union": {
        "n": 30,
        "mean_base": np.array([
            2.5, 2.6, 2.5,   # D1: weakest data
            2.4, 2.4, 2.5,   # D2: weakest tech
            2.6, 2.6, 2.5,   # D3: weakest compliance
            2.7, 2.6, 2.7,   # D4: limited resources
            2.6, 2.5, 2.6,   # D5: basic accountability
        ]),
    },
}
 
# ── Size distribution (spec Section 4.2) ─────────────────────────────
SIZE_CONFIG = {
    "large": {"n": 45, "size_boost":  0.6},
    "mid":   {"n": 60, "size_boost":  0.1},
    "small": {"n": 45, "size_boost": -0.3},
}
 
 
# ── Correlation matrix (15x15, positive semi-definite) ───────────────
 
def _build_cov_matrix(std: float = 0.85) -> np.ndarray:
    """Build a PSD covariance matrix encoding realistic indicator correlations.
 
    Key correlations (from spec Section 4):
      - data_governance   <-> audit_trail        (high:  0.55)
      - fca_alignment     <-> consumer_duty       (high:  0.70)
      - system_capability <-> ai_tooling          (high:  0.75)
      - regulatory D3     <-> ethical governance  (mod:   0.45)
    """
    C = np.eye(15)
 
    def _s(i, j, v):
        C[i, j] = v
        C[j, i] = v
 
    # D1 internal
    _s(0, 1, 0.65); _s(0, 2, 0.55); _s(1, 2, 0.60)
    # D2 internal
    _s(3, 4, 0.75); _s(3, 5, 0.55); _s(4, 5, 0.50)
    # D3 internal
    _s(6, 7, 0.70); _s(6, 8, 0.60); _s(7, 8, 0.65)
    # D4 internal
    _s(9, 10, 0.60); _s(9, 11, 0.50); _s(10, 11, 0.65)
    # D5 internal
    _s(12, 13, 0.70); _s(12, 14, 0.55); _s(13, 14, 0.60)
    # Cross-dimension (spec: regulatory <-> ethical governance)
    _s(1,  8,  0.55)   # data_governance <-> audit_trail
    _s(6,  12, 0.45)   # fca_alignment   <-> bias_mitigation
    _s(7,  13, 0.45)   # consumer_duty   <-> explainability
    _s(8,  14, 0.50)   # audit_trail     <-> accountability
    _s(3,  9,  0.40)   # system_capability <-> talent_readiness
    _s(4,  13, 0.45)   # ai_tooling      <-> explainability
    _s(11, 6,  0.40)   # leadership      <-> fca_alignment
 
    # Fix to nearest PSD via eigenvalue clipping (Higham approximation)
    eigvals, eigvecs = np.linalg.eigh(C)
    eigvals_clipped  = np.clip(eigvals, 1e-6, None)
    C_psd = eigvecs @ np.diag(eigvals_clipped) @ eigvecs.T
    # Re-normalise diagonal to 1.0
    D = np.diag(1.0 / np.sqrt(np.diag(C_psd)))
    C_psd = D @ C_psd @ D
 
    # Convert to covariance
    S = np.diag([std] * 15)
    return S @ C_psd @ S
 
 
# ── Institution name generator 
_SUFFIXES = [
    "Credit Solutions", "Finance Group", "Capital Services",
    "Lending Partners", "Debt Management", "Financial Services",
    "Money Solutions", "Credit Management", "Asset Finance",
    "Recovery Services", "Funding Group", "Capital Management",
]
 
 
def _make_name(used: set) -> str:
    """Generate a unique synthetic UK institution name using Faker."""
    for _ in range(200):
        name = f"{fake.last_name()} {_SUFFIXES[np.random.randint(0, len(_SUFFIXES))]}"
        if name not in used:
            used.add(name)
            return name
    return f"UK Institution {len(used) + 1}"
 
 
#  Main generator 
 
def generate_synthetic_institutions(
    output_path: str = "data/synthetic_institutions.csv",
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate 150 synthetic UK debt management institution profiles.
 
    Args:
        output_path: Where to write the CSV (relative to project root).
        seed:        Random seed — default 42 for full reproducibility.
 
    Returns:
        pd.DataFrame — 150 rows, 19 raw columns (no score columns).
        Score columns are added downstream by AIRIScorer.
    """
    rng = np.random.default_rng(seed)
 
    # Re-seed globals for reproducibility on repeated calls
    random.seed(seed)
    np.random.seed(seed)
    fake.seed_instance(seed)
 
    cov = _build_cov_matrix(std=0.85)
 
    # Pre-build size pool and shuffle
    size_pool = (["large"] * 45 + ["mid"] * 60 + ["small"] * 45)
    rng.shuffle(size_pool)
    size_pool = list(size_pool)
 
    all_rows   = []
    used_names = set()
 
    for sector, s_cfg in SECTOR_CONFIG.items():
        n_sector   = s_cfg["n"]
        mean_base  = s_cfg["mean_base"]
 
        for _ in range(n_sector):
            inst_size  = size_pool.pop(0)
            size_boost = SIZE_CONFIG[inst_size]["size_boost"]
 
            # Per-institution mean: sector base + size adjustment, clipped to [1.2, 4.8]
            mean_raw = np.clip(mean_base + size_boost, 1.2, 4.8)
 
            # Sample from multivariate normal, round and clip to Likert [1, 5]
            sample = rng.multivariate_normal(mean=mean_raw, cov=cov)
            sample = np.clip(np.round(sample), 1, 5).astype(int)
 
            row = {
                "institution_id":   f"INST_{len(all_rows) + 1:03d}",
                "institution_name": _make_name(used_names),
                "sector":           sector,
                "institution_size": inst_size,
            }
            for col, val in zip(INDICATORS, sample):
                row[col] = int(val)
 
            all_rows.append(row)
 
    df = pd.DataFrame(all_rows)
 
    # Shuffle rows so sectors aren't sequential
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
 
    # Re-assign IDs sequentially after shuffle
    df["institution_id"] = [f"INST_{i + 1:03d}" for i in range(len(df))]
 
    # Write CSV
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
 
    return df
 
 
# ── CLI entry point 
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 
    print("Generating synthetic dataset...")
    df = generate_synthetic_institutions()
    print(f"Done — {len(df)} institutions saved to data/synthetic_institutions.csv")
    print()
    print("Sector distribution:")
    print(df["sector"].value_counts().to_string())
    print()
    print("Size distribution:")
    print(df["institution_size"].value_counts().to_string())
    print()
    print("Indicator means (should differ meaningfully across sectors):")
    print(df.groupby("sector")[INDICATORS].mean().round(2).to_string())
    print()
    print("describe():")
    print(df[INDICATORS].describe().round(2).to_string())
 