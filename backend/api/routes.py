import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class DurationRequest(BaseModel):
    case_type: str
    court: str
    judge: str
    act: str
    num_hearings: int = 5


class DurationResponse(BaseModel):
    predicted_duration_days: float
    confidence: float
    explanation: dict


class OutcomeRequest(BaseModel):
    case_type: str
    judge: str
    act: str
    judgment_text: str = ""


class OutcomeResponse(BaseModel):
    predicted_outcome: str
    confidence: float
    explanation: dict


class SimilarCasesRequest(BaseModel):
    judgment_text: str
    top_k: int = 5


class SummarizeRequest(BaseModel):
    judgment_text: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str


# ---------------------------------------------------------------------------
# Dependency: shared app state injected from main.py
# ---------------------------------------------------------------------------

def get_app_state():
    from backend.main import app
    return app.state


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.post("/predict-duration", response_model=DurationResponse)
def predict_duration(req: DurationRequest, db: Session = Depends(get_db)):
    """Predict case duration given case metadata."""
    try:
        state = get_app_state()
        fe = state.feature_engineer
        dp = state.duration_predictor

        features = {
            "case_type_enc": fe.encode_single("case_type", req.case_type),
            "court_enc": fe.encode_single("court", req.court),
            "judge_enc": fe.encode_single("judge", req.judge),
            "act_enc": fe.encode_single("act", req.act),
            "num_hearings": req.num_hearings,
        }

        if dp.model is None:
            raise HTTPException(status_code=503, detail="Duration model not trained yet. Call /models/retrain first.")

        predicted = dp.predict(features)
        explanation = dp.explain(features)
        max_val = max(abs(v) for v in explanation.values()) if explanation else 1
        confidence = round(min(0.99, max(0.50, 1.0 - (max_val / (predicted + 1)))), 4)

        return {"predicted_duration_days": predicted, "confidence": confidence, "explanation": explanation}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/predict-duration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-outcome", response_model=OutcomeResponse)
def predict_outcome(req: OutcomeRequest, db: Session = Depends(get_db)):
    """Predict case outcome given case metadata and optional judgment text."""
    try:
        state = get_app_state()
        fe = state.feature_engineer
        op = state.outcome_predictor

        features = {
            "case_type_enc": fe.encode_single("case_type", req.case_type),
            "court_enc": fe.encode_single("court", "Unknown"),
            "judge_enc": fe.encode_single("judge", req.judge),
            "act_enc": fe.encode_single("act", req.act),
            "num_hearings": 5,
        }

        if op.model is None:
            raise HTTPException(status_code=503, detail="Outcome model not trained yet. Call /models/retrain first.")

        label, confidence = op.predict(features)
        explanation = op.explain(features)

        return {"predicted_outcome": label, "confidence": confidence, "explanation": explanation}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/predict-outcome error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar-cases")
def similar_cases(req: SimilarCasesRequest):
    """Retrieve similar cases using FAISS semantic search."""
    try:
        state = get_app_state()
        retriever = state.similar_case_retriever
        results = retriever.search(req.judgment_text, top_k=req.top_k)
        return {"similar_cases": [
            {"case_id": r["case_id"], "similarity_score": r["similarity_score"], "summary": r["text"]}
            for r in results
        ]}
    except Exception as e:
        logger.error(f"/similar-cases error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize")
def summarize_judgment(req: SummarizeRequest):
    """Extractive summarization of a judgment text."""
    try:
        state = get_app_state()
        summarizer = state.summarizer
        result = summarizer.summarize(req.judgment_text)
        return result
    except Exception as e:
        logger.error(f"/summarize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    """Return full judicial analytics."""
    try:
        state = get_app_state()
        analyst = state.analytics
        return analyst.get_all(db)
    except Exception as e:
        logger.error(f"/analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/case/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Retrieve full details for a specific case."""
    try:
        from backend.database.models import Case, Judgment
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        judgment = db.query(Judgment).filter(Judgment.case_id == case_id).first()
        return {
            "case_id": case.case_id,
            "court": case.court,
            "case_type": case.case_type,
            "filing_date": case.filing_date.isoformat() if case.filing_date else None,
            "decision_date": case.decision_date.isoformat() if case.decision_date else None,
            "duration_days": case.duration_days,
            "judge": case.judge,
            "petitioner": case.petitioner,
            "respondent": case.respondent,
            "act": case.act,
            "outcome": case.outcome,
            "num_hearings": case.num_hearings,
            "judgment_text": judgment.judgment_text if judgment else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/case/{case_id} error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/csv")
async def ingest_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and ingest a CSV file of court cases."""
    import io
    import pandas as pd
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        from backend.modules.data_ingestion import DataIngestionService
        svc = DataIngestionService(db_session=db)
        df = svc._clean_dataframe(df)
        count = svc.process_and_store(df)
        return {"message": f"CSV ingested successfully", "cases_loaded": count}
    except Exception as e:
        logger.error(f"/ingest/csv error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/retrain")
def retrain_models(db: Session = Depends(get_db)):
    """Retrain all ML models from current database / sample data."""
    try:
        import os
        import pandas as pd
        from backend.modules.feature_engineering import FeatureEngineer
        from backend.modules.duration_model import DurationPredictor
        from backend.modules.outcome_model import OutcomePredictor

        # Load data
        df = _load_training_data(db)
        if df.empty or len(df) < 10:
            raise HTTPException(status_code=400, detail="Not enough data to train models.")

        state = get_app_state()
        fe = FeatureEngineer()
        X_dur, y_dur, X_out, y_out = fe.prepare_training_data(df)
        state.feature_engineer = fe

        dur_metrics, out_metrics = {}, {}

        dp = DurationPredictor()
        if len(X_dur) >= 10:
            dur_metrics = dp.train(X_dur, y_dur)
        state.duration_predictor = dp

        op = OutcomePredictor()
        if len(X_out) >= 10:
            out_metrics = op.train(X_out, y_out)
        state.outcome_predictor = op

        # Rebuild FAISS index
        texts = df.get("judgment_text", pd.Series(dtype=str)).fillna("").tolist()
        case_ids = df.get("case_id", pd.Series(dtype=str)).astype(str).tolist()
        state.similar_case_retriever.build_index(texts, case_ids)

        return {
            "message": "Models retrained successfully",
            "metrics": {
                "duration_model": dur_metrics,
                "outcome_model": out_metrics,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/models/retrain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _load_training_data(db: Session):
    """Load cases from DB, falling back to sample CSV."""
    import pandas as pd
    try:
        from backend.database.models import Case, Judgment
        rows = db.query(Case).all()
        if rows:
            case_df = pd.DataFrame([{
                "case_id": r.case_id, "court": r.court, "case_type": r.case_type,
                "judge": r.judge, "act": r.act, "outcome": r.outcome,
                "duration_days": r.duration_days, "num_hearings": r.num_hearings,
                "filing_date": r.filing_date, "decision_date": r.decision_date,
            } for r in rows])
            judgments = db.query(Judgment).all()
            judg_df = pd.DataFrame([{"case_id": j.case_id, "judgment_text": j.judgment_text} for j in judgments])
            if not judg_df.empty:
                case_df = case_df.merge(judg_df, on="case_id", how="left")
            return case_df
    except Exception as e:
        logger.warning(f"DB load for training failed: {e}")

    csv_path = "data/sample_cases.csv"
    if not __import__("os").path.exists(csv_path):
        csv_path = "/app/data/sample_cases.csv"
    if __import__("os").path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()
