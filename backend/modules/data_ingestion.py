import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Handles loading of case data from CSV, Excel, and PDF formats."""

    def __init__(self, db_session=None):
        self.db = db_session

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load a CSV file and return a cleaned DataFrame."""
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return self._clean_dataframe(df)
        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {e}")
            raise

    def load_excel(self, file_path: str) -> pd.DataFrame:
        """Load an Excel file and return a cleaned DataFrame."""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return self._clean_dataframe(df)
        except Exception as e:
            logger.error(f"Error loading Excel {file_path}: {e}")
            raise

    def load_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            import PyPDF2
            text_parts = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            full_text = "\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from {file_path}")
            return full_text
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and fill missing values."""
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        for col in ["filing_date", "decision_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        for col in ["duration_days", "num_hearings"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        for col in ["court", "case_type", "judge", "petitioner", "respondent", "act", "outcome"]:
            if col in df.columns:
                df[col] = df[col].fillna("Unknown").astype(str).str.strip()
        return df

    def process_and_store(self, df: pd.DataFrame) -> int:
        """Process a DataFrame and persist rows to the database. Returns count inserted."""
        if self.db is None:
            logger.warning("No DB session provided; skipping database storage.")
            return 0

        from backend.database.models import Case, Judgment

        inserted = 0
        for _, row in df.iterrows():
            try:
                case_id = str(row.get("case_id", f"AUTO-{inserted}"))
                existing = self.db.query(Case).filter(Case.case_id == case_id).first()
                if existing:
                    continue

                case = Case(
                    case_id=case_id,
                    court=str(row.get("court", "Unknown")),
                    case_type=str(row.get("case_type", "Civil")),
                    filing_date=row.get("filing_date") if pd.notna(row.get("filing_date")) else datetime.utcnow(),
                    decision_date=row.get("decision_date") if pd.notna(row.get("decision_date")) else None,
                    duration_days=int(row.get("duration_days", 0)),
                    judge=str(row.get("judge", "Unknown")),
                    petitioner=str(row.get("petitioner", "")),
                    respondent=str(row.get("respondent", "")),
                    act=str(row.get("act", "")),
                    outcome=str(row.get("outcome", "")),
                    num_hearings=int(row.get("num_hearings", 0)),
                )
                self.db.add(case)

                judgment_text = str(row.get("judgment_text", ""))
                if judgment_text and judgment_text != "nan":
                    judgment = Judgment(case_id=case_id, judgment_text=judgment_text)
                    self.db.add(judgment)

                inserted += 1
            except Exception as e:
                logger.error(f"Error inserting case {row.get('case_id', '?')}: {e}")
                self.db.rollback()
                continue

        self.db.commit()
        logger.info(f"Stored {inserted} new cases in the database.")
        return inserted
