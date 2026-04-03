import logging
import os
from typing import Tuple

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

FEATURE_COLS = ["case_type_enc", "court_enc", "judge_enc", "act_enc", "num_hearings"]


class OutcomePredictor:
    """Predicts case outcome using XGBoost classifier with TF-IDF text features."""

    def __init__(self, model_path: str = "models/outcome_model.joblib"):
        self.model_path = model_path
        self.model = None
        self.tfidf = None
        self.label_encoder = None

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train XGBoost classifier and persist the model."""
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.preprocessing import LabelEncoder

        X_feat = X[[c for c in FEATURE_COLS if c in X.columns]].fillna(0)

        self.label_encoder = LabelEncoder()
        y_enc = self.label_encoder.fit_transform(y.astype(str))

        X_train, X_test, y_train, y_test = train_test_split(X_feat, y_enc, test_size=0.2, random_state=42)

        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            verbosity=0,
        )
        self.model.fit(X_train, y_train)

        os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
        joblib.dump({"model": self.model, "label_encoder": self.label_encoder}, self.model_path)
        logger.info(f"Outcome model saved to {self.model_path}")

        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        metrics = {
            "accuracy": round(float(acc), 4),
            "weighted_f1": round(float(report.get("weighted avg", {}).get("f1-score", 0.0)), 4),
        }
        logger.info(f"Outcome model metrics: {metrics}")
        return metrics

    def predict(self, features_dict: dict) -> Tuple[str, float]:
        """Return (outcome_label, confidence) for the given feature dict."""
        if self.model is None:
            self.load_model()
        X = self._dict_to_array(features_dict)
        pred_idx = self.model.predict(X)[0]
        probas = self.model.predict_proba(X)[0]
        confidence = float(np.max(probas))
        if self.label_encoder is not None:
            label = str(self.label_encoder.inverse_transform([pred_idx])[0])
        else:
            label = str(pred_idx)
        return label, round(confidence, 4)

    def explain(self, features_dict: dict) -> dict:
        """Return feature importances for the given prediction."""
        if self.model is None:
            self.load_model()
        try:
            feature_names = [c for c in FEATURE_COLS if c in features_dict or True][:len(FEATURE_COLS)]
            importances = self.model.feature_importances_
            return {feature_names[i]: round(float(importances[i]), 4) for i in range(min(len(feature_names), len(importances)))}
        except Exception as e:
            logger.warning(f"Feature importance failed: {e}")
            return {}

    def load_model(self):
        """Load saved model and label encoder from disk."""
        if os.path.exists(self.model_path):
            data = joblib.load(self.model_path)
            self.model = data["model"]
            self.label_encoder = data.get("label_encoder")
            logger.info(f"Outcome model loaded from {self.model_path}")
        else:
            logger.warning(f"Outcome model not found at {self.model_path}")

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """Evaluate on a test set and return metrics."""
        from sklearn.metrics import accuracy_score, classification_report
        if self.model is None:
            self.load_model()
        X = X_test[[c for c in FEATURE_COLS if c in X_test.columns]].fillna(0)
        if self.label_encoder is not None:
            y_enc = self.label_encoder.transform(y_test.astype(str))
        else:
            y_enc = y_test
        y_pred = self.model.predict(X)
        acc = accuracy_score(y_enc, y_pred)
        report = classification_report(y_enc, y_pred, output_dict=True, zero_division=0)
        return {
            "accuracy": round(float(acc), 4),
            "weighted_f1": round(float(report.get("weighted avg", {}).get("f1-score", 0.0)), 4),
        }

    def _dict_to_array(self, features_dict: dict) -> pd.DataFrame:
        row = {col: features_dict.get(col, 0) for col in FEATURE_COLS}
        return pd.DataFrame([row])
