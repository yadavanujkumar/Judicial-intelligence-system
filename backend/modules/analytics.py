import logging
from datetime import datetime
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class JudicialAnalytics:
    """Computes analytics on judicial case data from DB or an in-memory DataFrame."""

    def __init__(self, fallback_df: Optional[pd.DataFrame] = None):
        self.fallback_df = fallback_df

    def _get_df(self, db) -> pd.DataFrame:
        """Return a DataFrame of cases either from DB or fallback."""
        if db is not None:
            try:
                from backend.database.models import Case
                rows = db.query(Case).all()
                if rows:
                    return pd.DataFrame([{
                        "case_id": r.case_id,
                        "court": r.court,
                        "case_type": r.case_type,
                        "judge": r.judge,
                        "outcome": r.outcome,
                        "duration_days": r.duration_days,
                        "num_hearings": r.num_hearings,
                        "filing_date": r.filing_date,
                        "decision_date": r.decision_date,
                    } for r in rows])
            except Exception as e:
                logger.warning(f"DB query failed, using fallback: {e}")
        if self.fallback_df is not None:
            return self.fallback_df.copy()
        return pd.DataFrame()

    def get_court_analytics(self, db=None) -> list:
        df = self._get_df(db)
        if df.empty:
            return []
        grouped = df.groupby("court").agg(
            avg_duration=("duration_days", "mean"),
            total_cases=("case_id", "count"),
        ).reset_index()
        pending = df[df["outcome"].isna() | (df["outcome"] == "")].groupby("court").size().reset_index(name="pending_cases")
        result = grouped.merge(pending, on="court", how="left").fillna({"pending_cases": 0})
        return result.to_dict(orient="records")

    def get_judge_analytics(self, db=None) -> list:
        df = self._get_df(db)
        if df.empty:
            return []
        grouped = df.groupby("judge").agg(
            total_cases=("case_id", "count"),
            avg_duration=("duration_days", "mean"),
        ).reset_index()
        return grouped.sort_values("total_cases", ascending=False).head(20).to_dict(orient="records")

    def get_case_type_distribution(self, db=None) -> list:
        df = self._get_df(db)
        if df.empty:
            return []
        dist = df["case_type"].value_counts().reset_index()
        dist.columns = ["case_type", "count"]
        return dist.to_dict(orient="records")

    def get_backlog_analysis(self, db=None) -> list:
        df = self._get_df(db)
        if df.empty:
            return []
        pending_mask = df["outcome"].isna() | (df["outcome"].astype(str).str.strip() == "")
        backlog = df[pending_mask].groupby("court").size().reset_index(name="backlog_cases")
        total = df.groupby("court").size().reset_index(name="total_cases")
        merged = backlog.merge(total, on="court", how="left")
        merged["backlog_rate"] = (merged["backlog_cases"] / merged["total_cases"] * 100).round(2)
        return merged.sort_values("backlog_cases", ascending=False).to_dict(orient="records")

    def get_monthly_trends(self, db=None) -> list:
        df = self._get_df(db)
        if df.empty:
            return []
        df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")
        df["month"] = df["filing_date"].dt.to_period("M").astype(str)
        monthly = df.groupby("month").agg(
            filings=("case_id", "count"),
        ).reset_index()
        return monthly.sort_values("month").tail(24).to_dict(orient="records")

    def get_outcome_distribution(self, db=None) -> list:
        df = self._get_df(db)
        if df.empty:
            return []
        dist = df["outcome"].value_counts().reset_index()
        dist.columns = ["outcome", "count"]
        return dist.to_dict(orient="records")

    def get_all(self, db=None) -> dict:
        return {
            "court_analytics": self.get_court_analytics(db),
            "judge_analytics": self.get_judge_analytics(db),
            "case_type_distribution": self.get_case_type_distribution(db),
            "backlog_analysis": self.get_backlog_analysis(db),
            "monthly_trends": self.get_monthly_trends(db),
            "outcome_distribution": self.get_outcome_distribution(db),
        }
