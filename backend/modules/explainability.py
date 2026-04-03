import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """Generates SHAP-based or fallback explanations for ML predictions."""

    def explain_duration(self, model: Any, features: dict) -> dict:
        """Return SHAP values for duration prediction features."""
        try:
            import shap
            import pandas as pd
            feature_cols = ["case_type_enc", "court_enc", "judge_enc", "act_enc", "num_hearings"]
            X = pd.DataFrame([{col: features.get(col, 0) for col in feature_cols}])
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            return {feature_cols[i]: round(float(shap_values[0][i]), 4) for i in range(len(feature_cols))}
        except Exception as e:
            logger.warning(f"SHAP duration explanation failed: {e}")
            return self._fallback_importance(model, features)

    def explain_outcome(self, model: Any, features: dict) -> dict:
        """Return feature importances for outcome prediction."""
        try:
            import shap
            import pandas as pd
            feature_cols = ["case_type_enc", "court_enc", "judge_enc", "act_enc", "num_hearings"]
            X = pd.DataFrame([{col: features.get(col, 0) for col in feature_cols}])
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_arr = np.mean([np.abs(sv) for sv in shap_values], axis=0)
            else:
                shap_arr = np.abs(shap_values[0])
            return {feature_cols[i]: round(float(shap_arr[i]), 4) for i in range(len(feature_cols))}
        except Exception as e:
            logger.warning(f"SHAP outcome explanation failed: {e}")
            return self._fallback_importance(model, features)

    def _fallback_importance(self, model: Any, features: dict) -> dict:
        feature_cols = ["case_type_enc", "court_enc", "judge_enc", "act_enc", "num_hearings"]
        try:
            if hasattr(model, "feature_importances_"):
                return {feature_cols[i]: round(float(v), 4) for i, v in enumerate(model.feature_importances_)}
        except Exception:
            pass
        return {col: round(1.0 / len(feature_cols), 4) for col in feature_cols}

    def get_confidence_score(self, probabilities: np.ndarray) -> float:
        """Return the top class probability as a confidence percentage."""
        try:
            return round(float(np.max(probabilities)) * 100, 2)
        except Exception:
            return 0.0
