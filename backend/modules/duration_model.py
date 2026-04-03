import logging
import os
from typing import Optional

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

FEATURE_COLS = ["case_type_enc", "court_enc", "judge_enc", "act_enc", "num_hearings"]


class DurationPredictor:
    """Predicts case duration in days using XGBoost / RandomForest ensemble."""

    def __init__(self, model_path: str = "models/duration_model.joblib"):
        self.model_path = model_path
        self.model = None
        self.feature_engineer = None

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train XGBoost and RandomForest; persist the best model."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        import xgboost as xgb

        X = X[FEATURE_COLS] if all(c in X.columns for c in FEATURE_COLS) else X
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        xgb_model = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42, verbosity=0)
        xgb_model.fit(X_train, y_train)

        rf_model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
        rf_model.fit(X_train, y_train)

        xgb_mae = mean_absolute_error(y_test, xgb_model.predict(X_test))
        rf_mae = mean_absolute_error(y_test, rf_model.predict(X_test))

        self.model = xgb_model if xgb_mae <= rf_mae else rf_model
        best_name = "XGBoost" if xgb_mae <= rf_mae else "RandomForest"

        os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
        joblib.dump(self.model, self.model_path)
        logger.info(f"Duration model ({best_name}) saved to {self.model_path}")

        y_pred = self.model.predict(X_test)
        metrics = {
            "model": best_name,
            "MAE": round(float(mean_absolute_error(y_test, y_pred)), 2),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
            "R2": round(float(r2_score(y_test, y_pred)), 4),
        }
        logger.info(f"Duration model metrics: {metrics}")
        return metrics

    def predict(self, features_dict: dict) -> float:
        """Return predicted duration in days for the given feature dict."""
        if self.model is None:
            self.load_model()
        X = self._dict_to_array(features_dict)
        pred = float(self.model.predict(X)[0])
        if pred <= 0:
            logger.warning(f"Model predicted non-positive duration ({pred:.2f}); clamping to 1.0 day")
        return max(1.0, round(pred, 1))

    def explain(self, features_dict: dict) -> dict:
        """Return SHAP feature importances for the given input."""
        try:
            import shap
            if self.model is None:
                self.load_model()
            X = self._dict_to_array(features_dict)
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(X)
            feature_names = FEATURE_COLS
            return {
                feature_names[i]: round(float(shap_values[0][i]), 4)
                for i in range(len(feature_names))
            }
        except Exception as e:
            logger.warning(f"SHAP explanation failed: {e}")
            return self._fallback_importance(features_dict)

    def _fallback_importance(self, features_dict: dict) -> dict:
        """Return model feature importances when SHAP is unavailable."""
        try:
            if hasattr(self.model, "feature_importances_"):
                return {FEATURE_COLS[i]: round(float(v), 4) for i, v in enumerate(self.model.feature_importances_)}
        except Exception:
            pass
        return {col: 0.0 for col in FEATURE_COLS}

    def load_model(self):
        """Load a saved model from disk."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info(f"Duration model loaded from {self.model_path}")
        else:
            logger.warning(f"Duration model not found at {self.model_path}")

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """Evaluate on a test set and return metrics."""
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        if self.model is None:
            self.load_model()
        X = X_test[FEATURE_COLS] if all(c in X_test.columns for c in FEATURE_COLS) else X_test
        y_pred = self.model.predict(X)
        return {
            "MAE": round(float(mean_absolute_error(y_test, y_pred)), 2),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
            "R2": round(float(r2_score(y_test, y_pred)), 4),
        }

    def _dict_to_array(self, features_dict: dict) -> pd.DataFrame:
        row = {col: features_dict.get(col, 0) for col in FEATURE_COLS}
        return pd.DataFrame([row])
