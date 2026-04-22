"""XGBoost instance explanations for Streamlit (SHAP + safe fallbacks).

TreeExplainer can fail on some XGBoost/sklearn pickles (e.g. multiclass base_score
stored as a string) *during construction*. Callers must catch that and fall back.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Tuple

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

ExplainMethod = Literal["shap", "xgb_contrib"]


def load_xgb_classifier(project_root: Path):
    """Prefer native JSON (portable across XGBoost versions), else joblib pickle."""
    root = Path(project_root)
    json_path = root / "models" / "xgb_model.json"
    pkl_path = root / "models" / "xgb_model.pkl"
    if json_path.exists():
        clf = xgb.XGBClassifier()
        clf.load_model(str(json_path))
        return clf
    return joblib.load(pkl_path)


def _pred_class_from_model(xgb_model, x_input: np.ndarray) -> int:
    out = np.asarray(xgb_model.predict(x_input)).ravel()
    return int(out[0])


def _get_pred_class_shap_vector(shap_vals, pred_class: int, n_features: int) -> np.ndarray:
    """Return a 1D SHAP vector for the predicted class."""
    if isinstance(shap_vals, list):
        class_vals = np.asarray(shap_vals[pred_class]).squeeze()
        if class_vals.ndim == 1:
            return class_vals.astype(float)
        if class_vals.ndim == 2:
            if class_vals.shape[0] == n_features:
                return class_vals[:, 0].astype(float)
            if class_vals.shape[1] == n_features:
                return class_vals[0, :].astype(float)
        raise ValueError(f"Unsupported SHAP list shape: {class_vals.shape}")

    arr = np.asarray(shap_vals).squeeze()
    if arr.ndim == 1 and arr.shape[0] == n_features:
        return arr.astype(float)
    if arr.ndim == 2:
        if arr.shape[0] == n_features:
            if pred_class >= arr.shape[1]:
                raise ValueError(
                    f"Predicted class index {pred_class} out of bounds for SHAP shape {arr.shape}"
                )
            return arr[:, pred_class].astype(float)
        if arr.shape[1] == n_features:
            if pred_class >= arr.shape[0]:
                raise ValueError(
                    f"Predicted class index {pred_class} out of bounds for SHAP shape {arr.shape}"
                )
            return arr[pred_class, :].astype(float)
    raise ValueError(f"Unsupported SHAP output shape: {arr.shape}")


def _get_pred_class_xgb_contrib_vector(
    xgb_model,
    x_input: np.ndarray,
    pred_class: int,
    feature_names: list[str],
) -> np.ndarray:
    """SHAP-like per-feature contributions via XGBoost pred_contribs (bias omitted)."""
    n_features = len(feature_names)
    if x_input.ndim != 2 or x_input.shape[0] != 1:
        raise ValueError("x_input must be shape (1, n_features)")
    dmat = xgb.DMatrix(
        pd.DataFrame(x_input, columns=feature_names),
        enable_categorical=False,
    )
    contribs = np.asarray(
        xgb_model.get_booster().predict(
            dmat,
            pred_contribs=True,
            validate_features=False,
        )
    )

    if contribs.ndim == 3:
        row = contribs[0, pred_class, :]
    elif contribs.ndim == 2:
        row = contribs[0, :]
        base = n_features + 1
        if row.shape[0] == base:
            pass
        elif row.shape[0] % base == 0:
            n_classes = row.shape[0] // base
            if pred_class >= n_classes:
                raise ValueError(
                    f"Predicted class {pred_class} out of bounds for {n_classes} classes"
                )
            row = row.reshape(n_classes, base)[pred_class]
        else:
            n_classes = int(getattr(xgb_model, "n_classes_", 0) or 0)
            if n_classes <= 0:
                raise ValueError(f"Cannot parse contrib shape {contribs.shape}")
            expected_width = base * n_classes
            if row.shape[0] != expected_width:
                raise ValueError(f"Unsupported contrib shape: {contribs.shape}")
            row = row.reshape(n_classes, base)[pred_class]
    else:
        raise ValueError(f"Unsupported contrib ndim: {contribs.ndim}")

    return row[:n_features].astype(float)


def explain_instance(
    xgb_model,
    x_input: np.ndarray,
    feature_names: list[str],
) -> Tuple[np.ndarray, int, ExplainMethod]:
    """Return (per-feature contributions, predicted_class, method_used)."""
    n_features = len(feature_names)
    pred_class = _pred_class_from_model(xgb_model, x_input)
    try:
        explainer = shap.TreeExplainer(xgb_model)
        shap_vals = explainer.shap_values(x_input)
        sv = _get_pred_class_shap_vector(shap_vals, pred_class, n_features)
        return sv, pred_class, "shap"
    except Exception:
        sv = _get_pred_class_xgb_contrib_vector(
            xgb_model, x_input, pred_class, feature_names
        )
        return sv, pred_class, "xgb_contrib"
