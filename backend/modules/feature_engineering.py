import logging
import re
from datetime import datetime
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

CATEGORICAL_COLS = ["case_type", "court", "judge", "act", "outcome"]


class FeatureEngineer:
    """Builds features from raw case data for model training and inference."""

    def __init__(self):
        self.encoders: dict[str, LabelEncoder] = {}

    def calculate_duration(self, filing_date, decision_date) -> Optional[int]:
        """Return the number of days between two dates, or None if invalid."""
        try:
            if isinstance(filing_date, str):
                filing_date = datetime.fromisoformat(filing_date)
            if isinstance(decision_date, str):
                decision_date = datetime.fromisoformat(decision_date)
            if filing_date and decision_date:
                return max(0, (decision_date - filing_date).days)
        except Exception as e:
            logger.warning(f"Could not calculate duration: {e}")
        return None

    def encode_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Label-encode categorical columns. Fit encoders when fit=True."""
        df = df.copy()
        for col in CATEGORICAL_COLS:
            if col not in df.columns:
                continue
            df[col] = df[col].fillna("Unknown").astype(str)
            if fit:
                le = LabelEncoder()
                df[f"{col}_enc"] = le.fit_transform(df[col])
                self.encoders[col] = le
            else:
                if col in self.encoders:
                    le = self.encoders[col]
                    # Unknown categories are mapped to 0 (same as "Unknown" class used during fit)
                    df[f"{col}_enc"] = df[col].apply(
                        lambda x: int(le.transform([x])[0]) if x in le.classes_ else 0
                    )
                else:
                    df[f"{col}_enc"] = 0
        return df

    def encode_single(self, col: str, value: str) -> int:
        """Encode a single value using a fitted encoder."""
        if col not in self.encoders:
            return 0
        le = self.encoders[col]
        if value in le.classes_:
            return int(le.transform([value])[0])
        return 0

    def extract_text_features(self, text: str) -> dict:
        """Extract lightweight NLP features from judgment text."""
        if not text or text == "nan":
            return {"word_count": 0, "sentence_count": 0, "avg_word_len": 0}
        sentences = re.split(r"[.!?]+", text)
        words = text.split()
        avg_word_len = np.mean([len(w) for w in words]) if words else 0
        return {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_word_len": round(float(avg_word_len), 2),
        }

    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """
        Full pipeline: encode features and return (X_duration, y_duration, X_outcome, y_outcome).
        """
        df = df.copy()

        if "duration_days" not in df.columns and "filing_date" in df.columns and "decision_date" in df.columns:
            df["duration_days"] = df.apply(
                lambda r: self.calculate_duration(r["filing_date"], r["decision_date"]), axis=1
            )

        df = self.encode_features(df, fit=True)

        feature_cols_dur = [c for c in ["case_type_enc", "court_enc", "judge_enc", "act_enc", "num_hearings"] if c in df.columns]
        feature_cols_out = [c for c in ["case_type_enc", "court_enc", "judge_enc", "act_enc", "num_hearings"] if c in df.columns]

        df_dur = df.dropna(subset=["duration_days"])
        X_duration = df_dur[feature_cols_dur].fillna(0)
        y_duration = df_dur["duration_days"].astype(float)

        if "outcome" in df.columns and "outcome_enc" in df.columns:
            df_out = df.dropna(subset=["outcome"])
            X_outcome = df_out[feature_cols_out].fillna(0)
            y_outcome = df_out["outcome"].astype(str)
        else:
            X_outcome = pd.DataFrame()
            y_outcome = pd.Series(dtype=int)

        return X_duration, y_duration, X_outcome, y_outcome
