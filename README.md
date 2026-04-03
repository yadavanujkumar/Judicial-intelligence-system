# ⚖️ Judicial Intelligence System

An AI-powered platform for judicial analytics in India — predicting case durations, forecasting outcomes, retrieving similar precedents, and summarizing judgments.

---

## 🏗 Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    User / Browser                         │
└────────────────────┬──────────────────────────────────────┘
                     │ HTTP
          ┌──────────▼──────────┐
          │  Streamlit Dashboard │  :8501
          └──────────┬──────────┘
                     │ REST API
          ┌──────────▼──────────┐
          │   FastAPI Backend    │  :8000
          │  ┌───────────────┐  │
          │  │ Duration Model│  │  XGBoost / RandomForest
          │  │ Outcome Model │  │  XGBoost Classifier
          │  │ FAISS Index   │  │  Sentence Transformers
          │  │ Summarizer    │  │  Extractive NLP
          │  │ Analytics     │  │  Pandas aggregations
          │  └───────────────┘  │
          └──────────┬──────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼────┐   ┌──────▼──────┐  ┌────▼────┐
│PostgreSQL│   │  Prometheus  │  │ Grafana │
│  :5432  │   │    :9090     │  │  :3000  │
└─────────┘   └─────────────┘  └─────────┘
```

---

## 🚀 Quick Start

### Option 1 — Docker Compose (recommended)

```bash
git clone https://github.com/your-org/Judicial-intelligence-system.git
cd Judicial-intelligence-system

# Generate sample data
python scripts/generate_sample_data.py

# Start all services
docker compose up --build
```

| Service    | URL                      |
|------------|--------------------------|
| Dashboard  | http://localhost:8501    |
| Backend    | http://localhost:8000    |
| API Docs   | http://localhost:8000/docs |
| Prometheus | http://localhost:9090    |
| Grafana    | http://localhost:3000    |

### Option 2 — Local Development

```bash
# Python 3.11+ required
pip install -r requirements.txt

# Generate sample data
python scripts/generate_sample_data.py

# Start backend
uvicorn backend.main:app --reload --port 8000

# Start dashboard (new terminal)
streamlit run dashboard/app.py --server.port 8501
```

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI app entrypoint
│   ├── config.py               # Pydantic settings
│   ├── Dockerfile
│   ├── api/
│   │   └── routes.py           # All API endpoints
│   ├── database/
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── connection.py       # DB engine & session
│   ├── modules/
│   │   ├── data_ingestion.py   # CSV/Excel/PDF loading
│   │   ├── feature_engineering.py
│   │   ├── duration_model.py   # XGBoost duration predictor
│   │   ├── outcome_model.py    # XGBoost outcome classifier
│   │   ├── similar_cases.py    # FAISS semantic search
│   │   ├── summarization.py    # Extractive summarizer
│   │   ├── analytics.py        # Judicial statistics
│   │   └── explainability.py  # SHAP explanations
│   └── utils/
│       └── helpers.py
├── dashboard/
│   ├── app.py                  # Streamlit dashboard
│   └── Dockerfile
├── data/
│   └── sample_cases.csv        # 250 synthetic Indian court cases
├── scripts/
│   └── generate_sample_data.py
├── docker-compose.yml
├── prometheus.yml
└── requirements.txt
```

---

## 🔌 API Reference

### Health Check
```
GET /health
→ {"status": "healthy", "timestamp": "..."}
```

### Predict Case Duration
```
POST /predict-duration
Body: {"case_type": "Civil", "court": "Delhi High Court", "judge": "Justice D.Y. Chandrachud", "act": "CPC", "num_hearings": 10}
→ {"predicted_duration_days": 547.3, "confidence": 0.81, "explanation": {...}}
```

### Predict Case Outcome
```
POST /predict-outcome
Body: {"case_type": "Criminal", "judge": "Justice B.R. Gavai", "act": "IPC", "judgment_text": "..."}
→ {"predicted_outcome": "Acquitted", "confidence": 0.76, "explanation": {...}}
```

### Find Similar Cases
```
POST /similar-cases
Body: {"judgment_text": "The petitioner filed a civil suit...", "top_k": 5}
→ {"similar_cases": [{"case_id": "CS/1234/2021", "similarity_score": 0.93, "summary": "..."}]}
```

### Summarize Judgment
```
POST /summarize
Body: {"judgment_text": "Full judgment text..."}
→ {"summary": "...", "key_facts": "...", "legal_issues": "...", "final_decision": "...", "reasoning": "..."}
```

### Get Analytics
```
GET /analytics
→ {court_analytics, judge_analytics, case_type_distribution, backlog_analysis, monthly_trends, outcome_distribution}
```

### Ingest CSV
```
POST /ingest/csv
Form-data: file=<csv_file>
→ {"message": "CSV ingested successfully", "cases_loaded": 250}
```

### Retrain Models
```
GET /models/retrain
→ {"message": "Models retrained successfully", "metrics": {...}}
```

---

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| 🏠 Home / Overview | Key metrics, case type distribution, outcome charts |
| ⏱ Duration Prediction | Form input + SHAP bar chart explanation |
| 🎯 Outcome Prediction | Form input + confidence gauge |
| 🔍 Similar Case Search | FAISS semantic search results |
| 📝 Judgment Summarization | Extractive summary with structured sections |
| 📊 Judicial Analytics | Court/judge/trend charts |
| 📉 Court Backlog Analysis | Backlog heatmap and ranking |
| 🤖 Model Performance | MAE, RMSE, R², Accuracy, F1 gauges |

---

## 🤖 ML Models

### Duration Predictor
- **Algorithm:** XGBoost Regressor (vs. RandomForest, best selected)
- **Features:** case_type, court, judge, act, num_hearings (label-encoded)
- **Metrics (typical):** MAE ≈ 85–110 days, R² ≈ 0.70–0.80
- **Explainability:** SHAP TreeExplainer values

### Outcome Predictor
- **Algorithm:** XGBoost Classifier
- **Features:** case_type, court, judge, act, num_hearings
- **Metrics (typical):** Accuracy ≈ 75–85%, Weighted F1 ≈ 0.74–0.84

### Similar Case Retriever
- **Embedding Model:** `all-MiniLM-L6-v2` (Sentence Transformers, 384-dim)
- **Index:** FAISS IndexFlatIP (cosine similarity via normalized embeddings)

### Judgment Summarizer
- **Approach:** Extractive summarization with legal keyword scoring
- **No external API required** – fully local, lightweight

---

## 🗄 Database Schema

| Table | Key Columns |
|-------|-------------|
| `cases` | case_id, court, case_type, filing_date, decision_date, duration_days, judge, outcome |
| `judgments` | case_id, judgment_text, summary, embedding_json |
| `predictions` | case_id, predicted_duration, predicted_outcome, confidence |
| `analytics_records` | court, avg_duration, total_cases, pending_cases |

---

## 🌐 Data Sources

The system is pre-loaded with **250 synthetic Indian court cases** generated in `data/sample_cases.csv`, covering:

- **Courts:** Supreme Court, 14 High Courts
- **Case Types:** Civil, Criminal, Family, Tax, Consumer, Labour, Constitutional, Arbitration
- **Acts:** IPC, CPC, CrPC, Hindu Marriage Act, Income Tax Act, Consumer Protection Act, and more
- **Duration:** 30–3000 days
- **Outcomes:** Allowed, Dismissed, Convicted, Acquitted, Settled, and more

---

## 🔐 Security

- JWT-based authentication (configured via `SECRET_KEY`)
- API key header support
- CORS middleware (configurable)
- Prometheus metrics endpoint

---

## 🐳 Docker Services

| Service | Image | Port |
|---------|-------|------|
| PostgreSQL | `postgres:15` | 5432 |
| Backend | Custom Python 3.11 | 8000 |
| Dashboard | Custom Python 3.11 | 8501 |
| Prometheus | `prom/prometheus` | 9090 |
| Grafana | `grafana/grafana` | 3000 |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push and open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
