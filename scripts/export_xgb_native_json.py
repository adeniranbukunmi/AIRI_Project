#!/usr/bin/env python3
"""Write models/xgb_model.json from models/xgb_model.pkl for portable deploys.

Community Cloud may use a newer XGBoost than the version that pickled the model.
Native JSON loads cleanly across versions; run this once locally and commit the JSON.
"""
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parent.parent
PKL = ROOT / "models" / "xgb_model.pkl"
OUT = ROOT / "models" / "xgb_model.json"


def main() -> None:
    if not PKL.exists():
        raise SystemExit(f"Missing {PKL}")
    model = joblib.load(PKL)
    model.get_booster().save_model(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
