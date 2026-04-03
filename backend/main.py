import logging
import os
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan – startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Judicial Intelligence System starting ===")
    await _startup(app)
    yield
    logger.info("=== Judicial Intelligence System shutting down ===")


async def _startup(app: FastAPI):
    """Initialise DB, train models, build FAISS index on startup."""
    from backend.modules.feature_engineering import FeatureEngineer
    from backend.modules.duration_model import DurationPredictor
    from backend.modules.outcome_model import OutcomePredictor
    from backend.modules.similar_cases import SimilarCaseRetriever
    from backend.modules.summarization import JudgmentSummarizer
    from backend.modules.analytics import JudicialAnalytics

    # Attach service singletons to app.state so routes can access them.
    app.state.feature_engineer = FeatureEngineer()
    app.state.duration_predictor = DurationPredictor(settings.DURATION_MODEL_PATH)
    app.state.outcome_predictor = OutcomePredictor(settings.OUTCOME_MODEL_PATH)
    app.state.similar_case_retriever = SimilarCaseRetriever(
        model_name=settings.EMBEDDING_MODEL,
        index_path=settings.FAISS_INDEX_PATH,
    )
    app.state.summarizer = JudgmentSummarizer()
    app.state.analytics = JudicialAnalytics()

    # Initialise database tables
    try:
        from backend.database.connection import init_db
        init_db()
        logger.info("Database tables initialised.")
    except Exception as e:
        logger.warning(f"DB init failed (continuing without DB): {e}")

    # Load sample data from CSV
    df = _load_sample_data()

    if not df.empty:
        app.state.analytics = JudicialAnalytics(fallback_df=df)

        # Try to store in DB
        try:
            from backend.database.connection import SessionLocal
            from backend.modules.data_ingestion import DataIngestionService
            db = SessionLocal()
            svc = DataIngestionService(db_session=db)
            svc.process_and_store(df)
            db.close()
        except Exception as e:
            logger.warning(f"Could not seed DB from CSV: {e}")

        # Train models if not already saved
        fe = app.state.feature_engineer
        X_dur, y_dur, X_out, y_out = fe.prepare_training_data(df)

        dp = app.state.duration_predictor
        if not os.path.exists(settings.DURATION_MODEL_PATH) and len(X_dur) >= 10:
            logger.info("Training duration model …")
            dp.train(X_dur, y_dur)
        else:
            dp.load_model()

        op = app.state.outcome_predictor
        if not os.path.exists(settings.OUTCOME_MODEL_PATH) and len(X_out) >= 10:
            logger.info("Training outcome model …")
            op.train(X_out, y_out)
        else:
            op.load_model()

        # Build FAISS index
        retriever = app.state.similar_case_retriever
        retriever.load_index(settings.FAISS_INDEX_PATH)
        if retriever.index is None:
            logger.info("Building FAISS index …")
            texts = df.get("judgment_text", pd.Series(dtype=str)).fillna("").tolist()
            case_ids = df.get("case_id", pd.Series(dtype=str)).astype(str).tolist()
            built = retriever.build_index(texts, case_ids)
            if built:
                retriever.save_index(settings.FAISS_INDEX_PATH)

    logger.info("=== Startup complete ===")


def _load_sample_data() -> pd.DataFrame:
    """Load the bundled sample CSV, trying several candidate paths."""
    candidates = [
        "data/sample_cases.csv",
        "/app/data/sample_cases.csv",
        os.path.join(os.path.dirname(__file__), "..", "data", "sample_cases.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                logger.info(f"Loaded {len(df)} sample cases from {path}")
                return df
            except Exception as e:
                logger.warning(f"Could not read {path}: {e}")
    logger.warning("Sample CSV not found; starting with empty dataset.")
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Judicial Intelligence System",
    description="AI-powered judicial analytics: duration prediction, outcome forecasting, similar-case retrieval, and judgment summarization.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
    logger.info("Prometheus metrics enabled at /metrics")
except Exception as e:
    logger.warning(f"Prometheus instrumentation skipped: {e}")

# Routes
from backend.api.routes import router
app.include_router(router, prefix="")


# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})
