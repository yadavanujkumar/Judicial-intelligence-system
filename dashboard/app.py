"""
Judicial Intelligence System – Streamlit Dashboard
Works standalone with mock data when the backend is unavailable.
"""
import os
import random
from datetime import datetime, timedelta

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Judicial Intelligence System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {font-size: 2.2rem; font-weight: 700; color: #1a3a5c;}
    .sub-header {font-size: 1.1rem; color: #4a6fa5; margin-bottom: 1rem;}
    .metric-card {background: #f0f4ff; border-radius: 10px; padding: 1rem; text-align: center;}
    .section-title {font-size: 1.3rem; font-weight: 600; color: #1a3a5c; border-bottom: 2px solid #4a6fa5; padding-bottom: 0.3rem; margin-bottom: 1rem;}
    .highlight {background-color: #e8f4ea; border-left: 4px solid #2e7d32; padding: 0.5rem 1rem; border-radius: 4px;}
    .warning-box {background-color: #fff3e0; border-left: 4px solid #ef6c00; padding: 0.5rem 1rem; border-radius: 4px;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Backend connectivity helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def call_backend(method: str, path: str, payload: dict = None) -> tuple[dict | None, bool]:
    """Returns (data, is_mock). is_mock=True when backend is unreachable."""
    try:
        url = f"{BACKEND_URL}{path}"
        timeout = httpx.Timeout(10.0)
        if method == "GET":
            r = httpx.get(url, timeout=timeout)
        else:
            r = httpx.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json(), False
    except Exception:
        return None, True


# ---------------------------------------------------------------------------
# Mock data generators
# ---------------------------------------------------------------------------

COURTS = [
    "Supreme Court of India", "Delhi High Court", "Bombay High Court",
    "Madras High Court", "Calcutta High Court", "Allahabad High Court",
    "Karnataka High Court", "Rajasthan High Court", "Gujarat High Court",
    "Punjab & Haryana High Court",
]
CASE_TYPES = ["Civil", "Criminal", "Family", "Tax", "Consumer", "Labour", "Constitutional", "Arbitration"]
OUTCOMES = ["Allowed", "Dismissed", "Convicted", "Acquitted", "Settled", "Bail Granted", "Remanded"]
JUDGES = [
    "Justice D.Y. Chandrachud", "Justice Sanjiv Khanna", "Justice B.R. Gavai",
    "Justice Surya Kant", "Justice Hima Kohli", "Justice A.S. Bopanna",
    "Justice S.C. Sharma", "Justice Rajesh Bindal", "Justice Manmohan",
    "Justice Prathiba M. Singh",
]


def shorten_court_name(name: str) -> str:
    """Return an abbreviated court name for use in chart labels."""
    return name.replace(" High Court", " HC").replace("Supreme Court of India", "SC India")


def mock_analytics() -> dict:
    random.seed(42)
    court_analytics = [{
        "court": c,
        "avg_duration": random.randint(200, 1800),
        "total_cases": random.randint(50, 500),
        "pending_cases": random.randint(5, 100),
    } for c in COURTS]
    judge_analytics = [{
        "judge": j,
        "total_cases": random.randint(20, 200),
        "avg_duration": random.randint(150, 900),
    } for j in JUDGES]
    case_type_dist = [{"case_type": ct, "count": random.randint(30, 300)} for ct in CASE_TYPES]
    backlog = [{"court": c, "backlog_cases": random.randint(5, 80), "backlog_rate": random.uniform(5, 40)} for c in COURTS]
    months = [(datetime(2023, 1, 1) + timedelta(days=30 * i)).strftime("%Y-%m") for i in range(24)]
    monthly = [{"month": m, "filings": random.randint(20, 120)} for m in months]
    outcome_dist = [{"outcome": o, "count": random.randint(20, 200)} for o in OUTCOMES]
    return {
        "court_analytics": court_analytics,
        "judge_analytics": judge_analytics,
        "case_type_distribution": case_type_dist,
        "backlog_analysis": backlog,
        "monthly_trends": monthly,
        "outcome_distribution": outcome_dist,
    }


def mock_duration_prediction(case_type, court, judge, act, num_hearings) -> dict:
    base = {"Civil": 600, "Criminal": 800, "Family": 450, "Tax": 500, "Consumer": 300, "Labour": 700, "Constitutional": 900, "Arbitration": 400}
    pred = base.get(case_type, 500) + num_hearings * 15 + random.randint(-50, 50)
    return {
        "predicted_duration_days": float(pred),
        "confidence": round(random.uniform(0.72, 0.91), 2),
        "explanation": {
            "case_type_enc": round(random.uniform(0.3, 1.2), 3),
            "court_enc": round(random.uniform(0.1, 0.8), 3),
            "judge_enc": round(random.uniform(0.05, 0.6), 3),
            "act_enc": round(random.uniform(0.1, 0.7), 3),
            "num_hearings": round(random.uniform(0.2, 0.9), 3),
        },
    }


def mock_outcome_prediction(case_type, judge, act, text) -> dict:
    outcomes = {"Civil": "Dismissed", "Criminal": "Acquitted", "Family": "Settled",
                "Tax": "Allowed", "Consumer": "Allowed", "Labour": "Reinstated",
                "Constitutional": "Dismissed", "Arbitration": "Award Upheld"}
    return {
        "predicted_outcome": outcomes.get(case_type, "Dismissed"),
        "confidence": round(random.uniform(0.65, 0.92), 2),
        "explanation": {
            "case_type_enc": round(random.uniform(0.4, 1.5), 3),
            "judge_enc": round(random.uniform(0.1, 0.9), 3),
            "act_enc": round(random.uniform(0.15, 0.8), 3),
            "court_enc": round(random.uniform(0.1, 0.6), 3),
            "num_hearings": round(random.uniform(0.05, 0.4), 3),
        },
    }


def mock_similar_cases(text) -> dict:
    cases = [
        {"case_id": f"CS/{random.randint(1000,9999)}/2021", "similarity_score": round(random.uniform(0.7, 0.98), 3),
         "summary": "The petitioner filed a civil suit. The court held that the respondent had failed its obligation. The suit was allowed."},
        {"case_id": f"CR/{random.randint(1000,9999)}/2022", "similarity_score": round(random.uniform(0.6, 0.89), 3),
         "summary": "The accused was charged under IPC. Evidence was examined. The accused was acquitted."},
        {"case_id": f"WP/{random.randint(1000,9999)}/2020", "similarity_score": round(random.uniform(0.55, 0.85), 3),
         "summary": "A writ petition was filed challenging the provision. The court found it ultra vires. The petition was allowed."},
    ]
    return {"similar_cases": cases}


def mock_summary(text) -> dict:
    return {
        "summary": "The petitioner filed a case before the High Court seeking relief against the respondent. The court examined the evidence and legal submissions by both parties. Based on the legal provisions and precedents, the court passed the judgment.",
        "key_facts": "The petitioner alleged breach of statutory duty by the respondent authority. The respondent denied the allegations.",
        "legal_issues": "Whether the respondent violated the provisions of the applicable Act. Whether the petitioner was entitled to the relief claimed.",
        "final_decision": "The petition was allowed. The respondent was directed to comply with the statutory requirements within 30 days.",
        "reasoning": "The court held that the evidence on record clearly established the petitioner's case and the respondent had failed its legal obligation.",
    }


def mock_model_metrics() -> dict:
    return {
        "duration_model": {"model": "XGBoost", "MAE": 87.3, "RMSE": 134.2, "R2": 0.742},
        "outcome_model": {"accuracy": 0.783, "weighted_f1": 0.776},
    }


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

pages = [
    "🏠 Home / Overview",
    "⏱ Case Duration Prediction",
    "🎯 Case Outcome Prediction",
    "🔍 Similar Case Search",
    "📝 Judgment Summarization",
    "📊 Judicial Analytics",
    "📉 Court Backlog Analysis",
    "🤖 Model Performance",
]
st.sidebar.markdown("## ⚖️ Judicial Intelligence\n### System Navigation")
page = st.sidebar.radio("Select Page", pages, label_visibility="collapsed")

# Check backend health
health_data, is_mock_health = call_backend("GET", "/health")
if is_mock_health:
    st.sidebar.warning("⚠️ Backend offline – showing mock data")
else:
    st.sidebar.success("✅ Backend connected")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Backend URL:** `{BACKEND_URL}`")
st.sidebar.markdown("**Version:** 1.0.0")

# ---------------------------------------------------------------------------
# Page: Home / Overview
# ---------------------------------------------------------------------------

if page == "🏠 Home / Overview":
    st.markdown('<h1 class="main-header">⚖️ Judicial Intelligence System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered analytics for the Indian judiciary – predicting case durations, outcomes, finding similar cases, and summarizing judgments.</p>', unsafe_allow_html=True)

    analytics_data, is_mock = call_backend("GET", "/analytics")
    if is_mock or not analytics_data:
        analytics_data = mock_analytics()

    court_df = pd.DataFrame(analytics_data.get("court_analytics", []))
    total_cases = int(court_df["total_cases"].sum()) if not court_df.empty else 0
    avg_dur = int(court_df["avg_duration"].mean()) if not court_df.empty else 0
    pending = int(court_df["pending_cases"].sum()) if not court_df.empty else 0
    num_courts = len(court_df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 Total Cases", f"{total_cases:,}")
    with col2:
        st.metric("📅 Avg Duration (days)", f"{avg_dur:,}")
    with col3:
        st.metric("⏳ Pending Cases", f"{pending:,}")
    with col4:
        st.metric("🏛 Courts Covered", num_courts)

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<p class="section-title">Case Type Distribution</p>', unsafe_allow_html=True)
        ct_df = pd.DataFrame(analytics_data.get("case_type_distribution", []))
        if not ct_df.empty:
            fig = px.pie(ct_df, names="case_type", values="count", color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<p class="section-title">Outcome Distribution</p>', unsafe_allow_html=True)
        od_df = pd.DataFrame(analytics_data.get("outcome_distribution", []))
        if not od_df.empty:
            fig = px.bar(od_df.sort_values("count", ascending=True), x="count", y="outcome", orientation="h",
                         color="count", color_continuous_scale="Blues")
            fig.update_layout(margin=dict(t=20, b=20, l=0, r=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔑 Key Features")
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        st.info("⏱ **Duration Prediction**\nPredict case resolution time using XGBoost ML models with SHAP explanations.")
    with fcol2:
        st.info("🎯 **Outcome Prediction**\nForecast case outcomes with confidence scores and feature importance.")
    with fcol3:
        st.info("🔍 **Similar Cases**\nFind semantically similar precedents using FAISS vector search.")
    with fcol4:
        st.info("📝 **Summarization**\nAuto-extract key facts, legal issues, and decisions from judgments.")

# ---------------------------------------------------------------------------
# Page: Case Duration Prediction
# ---------------------------------------------------------------------------

elif page == "⏱ Case Duration Prediction":
    st.markdown('<h1 class="main-header">⏱ Case Duration Prediction</h1>', unsafe_allow_html=True)
    st.markdown("Predict how many days a case will take to resolve.")

    with st.form("duration_form"):
        col1, col2 = st.columns(2)
        with col1:
            case_type = st.selectbox("Case Type", CASE_TYPES)
            court = st.selectbox("Court", COURTS)
            judge = st.selectbox("Judge", JUDGES)
        with col2:
            act = st.selectbox("Applicable Act", [
                "Indian Penal Code (IPC)", "Code of Civil Procedure (CPC)",
                "Hindu Marriage Act, 1955", "Income Tax Act, 1961",
                "Consumer Protection Act, 2019", "Industrial Disputes Act, 1947",
                "Arbitration and Conciliation Act, 1996", "Companies Act, 2013",
                "Motor Vehicles Act, 1988", "POCSO Act, 2012",
            ])
            num_hearings = st.slider("Expected Number of Hearings", 1, 100, 10)
        submitted = st.form_submit_button("🔮 Predict Duration")

    if submitted:
        payload = {"case_type": case_type, "court": court, "judge": judge, "act": act, "num_hearings": num_hearings}
        result, is_mock = call_backend("POST", "/predict-duration", payload)
        if is_mock or not result:
            result = mock_duration_prediction(case_type, court, judge, act, num_hearings)
            st.caption("*(Mock prediction – backend offline)*")

        days = result["predicted_duration_days"]
        conf = result["confidence"]
        years = days / 365
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("📅 Predicted Duration", f"{int(days)} days")
        c2.metric("📆 Approx. Years", f"{years:.1f} years")
        c3.metric("🎯 Confidence", f"{conf * 100:.1f}%")

        st.markdown("#### SHAP Feature Contributions")
        exp = result.get("explanation", {})
        if exp:
            exp_df = pd.DataFrame(list(exp.items()), columns=["Feature", "SHAP Value"])
            exp_df = exp_df.sort_values("SHAP Value", ascending=True)
            colors = ["#d32f2f" if v < 0 else "#388e3c" for v in exp_df["SHAP Value"]]
            fig = go.Figure(go.Bar(x=exp_df["SHAP Value"], y=exp_df["Feature"], orientation="h", marker_color=colors))
            fig.update_layout(title="SHAP Values (positive = increases duration)", height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        if days > 1000:
            st.markdown('<div class="warning-box">⚠️ This case is predicted to take over 1000 days. Consider mediation or expedited hearing.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="highlight">✅ Case expected to resolve within a reasonable timeframe.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Page: Case Outcome Prediction
# ---------------------------------------------------------------------------

elif page == "🎯 Case Outcome Prediction":
    st.markdown('<h1 class="main-header">🎯 Case Outcome Prediction</h1>', unsafe_allow_html=True)
    st.markdown("Predict the likely outcome of a case.")

    with st.form("outcome_form"):
        col1, col2 = st.columns(2)
        with col1:
            case_type = st.selectbox("Case Type", CASE_TYPES)
            judge = st.selectbox("Presiding Judge", JUDGES)
        with col2:
            act = st.selectbox("Applicable Act", [
                "Indian Penal Code (IPC)", "Code of Civil Procedure (CPC)",
                "Hindu Marriage Act, 1955", "Income Tax Act, 1961",
                "Consumer Protection Act, 2019", "Industrial Disputes Act, 1947",
                "Arbitration and Conciliation Act, 1996",
            ])
        judgment_text = st.text_area("Judgment / Case Summary Text (optional)", height=150,
                                     placeholder="Enter case facts, arguments or partial judgment text…")
        submitted = st.form_submit_button("🔮 Predict Outcome")

    if submitted:
        payload = {"case_type": case_type, "judge": judge, "act": act, "judgment_text": judgment_text}
        result, is_mock = call_backend("POST", "/predict-outcome", payload)
        if is_mock or not result:
            result = mock_outcome_prediction(case_type, judge, act, judgment_text)
            st.caption("*(Mock prediction – backend offline)*")

        outcome = result["predicted_outcome"]
        confidence = result["confidence"]
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("⚖️ Predicted Outcome", outcome)
            st.metric("🎯 Confidence", f"{confidence * 100:.1f}%")
        with col2:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=confidence * 100,
                title={"text": "Confidence (%)"},
                gauge={"axis": {"range": [0, 100]},
                       "bar": {"color": "#1a73e8"},
                       "steps": [{"range": [0, 50], "color": "#ffcdd2"}, {"range": [50, 75], "color": "#fff9c4"}, {"range": [75, 100], "color": "#c8e6c9"}]},
            ))
            fig.update_layout(height=280, margin=dict(t=40, b=10, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Feature Importance")
        exp = result.get("explanation", {})
        if exp:
            exp_df = pd.DataFrame(list(exp.items()), columns=["Feature", "Importance"])
            exp_df = exp_df.sort_values("Importance", ascending=True)
            fig = px.bar(exp_df, x="Importance", y="Feature", orientation="h", color="Importance",
                         color_continuous_scale="Viridis")
            fig.update_layout(height=280, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Page: Similar Case Search
# ---------------------------------------------------------------------------

elif page == "🔍 Similar Case Search":
    st.markdown('<h1 class="main-header">🔍 Similar Case Search</h1>', unsafe_allow_html=True)
    st.markdown("Find semantically similar precedents using AI-powered search.")

    query_text = st.text_area("Enter judgment text or case description", height=180,
                              placeholder="The petitioner filed a civil suit seeking specific performance…")
    top_k = st.slider("Number of results", 1, 10, 5)

    if st.button("🔍 Search Similar Cases") and query_text.strip():
        with st.spinner("Searching …"):
            payload = {"judgment_text": query_text, "top_k": top_k}
            result, is_mock = call_backend("POST", "/similar-cases", payload)
            if is_mock or not result:
                result = mock_similar_cases(query_text)
                st.caption("*(Mock results – backend offline)*")

        cases = result.get("similar_cases", [])
        if cases:
            st.markdown(f"#### Found {len(cases)} Similar Cases")
            for i, case in enumerate(cases, 1):
                with st.expander(f"#{i} — {case['case_id']} (Similarity: {case['similarity_score']:.3f})", expanded=i == 1):
                    st.markdown(f"**Case ID:** `{case['case_id']}`")
                    st.markdown(f"**Similarity Score:** {case['similarity_score']:.4f}")
                    st.markdown(f"**Excerpt:** {case.get('summary', 'N/A')}")
        else:
            st.info("No similar cases found. Try with more descriptive text.")

# ---------------------------------------------------------------------------
# Page: Judgment Summarization
# ---------------------------------------------------------------------------

elif page == "📝 Judgment Summarization":
    st.markdown('<h1 class="main-header">📝 Judgment Summarization</h1>', unsafe_allow_html=True)
    st.markdown("Automatically extract key information from judgment text.")

    judgment_text = st.text_area("Paste the full judgment text below", height=250,
                                 placeholder="Enter the full judgment text here…")

    if st.button("📝 Summarize Judgment") and judgment_text.strip():
        with st.spinner("Analyzing judgment…"):
            payload = {"judgment_text": judgment_text}
            result, is_mock = call_backend("POST", "/summarize", payload)
            if is_mock or not result:
                result = mock_summary(judgment_text)
                st.caption("*(Mock summary – backend offline)*")

        st.markdown("---")
        st.markdown("### 📋 Summary")
        st.info(result.get("summary", "Not available."))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📌 Key Facts")
            st.write(result.get("key_facts", "Not available."))
            st.markdown("#### ⚖️ Legal Issues")
            st.write(result.get("legal_issues", "Not available."))
        with col2:
            st.markdown("#### 🏛 Final Decision")
            st.markdown(f'<div class="highlight">{result.get("final_decision", "Not available.")}</div>', unsafe_allow_html=True)
            st.markdown("#### 💡 Reasoning")
            st.write(result.get("reasoning", "Not available."))

# ---------------------------------------------------------------------------
# Page: Judicial Analytics
# ---------------------------------------------------------------------------

elif page == "📊 Judicial Analytics":
    st.markdown('<h1 class="main-header">📊 Judicial Analytics</h1>', unsafe_allow_html=True)

    data, is_mock = call_backend("GET", "/analytics")
    if is_mock or not data:
        data = mock_analytics()
        st.caption("*(Mock analytics – backend offline)*")

    tab1, tab2, tab3, tab4 = st.tabs(["🏛 Courts", "👨‍⚖️ Judges", "📈 Trends", "⚖️ Outcomes"])

    with tab1:
        st.markdown("#### Average Case Duration by Court")
        court_df = pd.DataFrame(data.get("court_analytics", []))
        if not court_df.empty:
            court_df = court_df.sort_values("avg_duration", ascending=False)
            court_df["court_short"] = court_df["court"].apply(shorten_court_name)
            fig = px.bar(court_df, x="court_short", y="avg_duration", color="avg_duration",
                         color_continuous_scale="RdYlGn_r", labels={"avg_duration": "Avg Duration (days)", "court_short": "Court"})
            fig.update_layout(xaxis_tickangle=-35, height=420, margin=dict(b=120))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(court_df[["court", "total_cases", "avg_duration", "pending_cases"]].rename(columns={
                "court": "Court", "total_cases": "Total Cases", "avg_duration": "Avg Duration (days)", "pending_cases": "Pending"}),
                use_container_width=True)

    with tab2:
        st.markdown("#### Judge Workload")
        judge_df = pd.DataFrame(data.get("judge_analytics", []))
        if not judge_df.empty:
            judge_df = judge_df.sort_values("total_cases", ascending=False).head(10)
            fig = px.bar(judge_df, x="total_cases", y="judge", orientation="h", color="avg_duration",
                         color_continuous_scale="Blues", labels={"total_cases": "Total Cases", "judge": "Judge", "avg_duration": "Avg Duration (days)"})
            fig.update_layout(height=400, margin=dict(l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("#### Monthly Filing Trends")
        monthly_df = pd.DataFrame(data.get("monthly_trends", []))
        if not monthly_df.empty:
            fig = px.line(monthly_df, x="month", y="filings", markers=True,
                          labels={"month": "Month", "filings": "Cases Filed"})
            fig.update_traces(line_color="#1a73e8", marker_color="#0d47a1")
            fig.update_layout(height=380, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown("#### Case Type Distribution")
        ct_df = pd.DataFrame(data.get("case_type_distribution", []))
        if not ct_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(ct_df, names="case_type", values="count", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(height=360, margin=dict(t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                od_df = pd.DataFrame(data.get("outcome_distribution", []))
                if not od_df.empty:
                    fig = px.bar(od_df.sort_values("count"), x="count", y="outcome", orientation="h", color="count",
                                 color_continuous_scale="Greens", labels={"count": "Cases", "outcome": "Outcome"})
                    fig.update_layout(height=360, margin=dict(t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Page: Court Backlog Analysis
# ---------------------------------------------------------------------------

elif page == "📉 Court Backlog Analysis":
    st.markdown('<h1 class="main-header">📉 Court Backlog Analysis</h1>', unsafe_allow_html=True)
    st.markdown("Identify courts with high case backlogs for prioritized intervention.")

    data, is_mock = call_backend("GET", "/analytics")
    if is_mock or not data:
        data = mock_analytics()
        st.caption("*(Mock data – backend offline)*")

    backlog_df = pd.DataFrame(data.get("backlog_analysis", []))
    if not backlog_df.empty:
        court_df = pd.DataFrame(data.get("court_analytics", []))
        if not court_df.empty and "total_cases" in court_df.columns:
            merged = backlog_df.merge(court_df[["court", "total_cases"]], on="court", how="left")
        else:
            merged = backlog_df.copy()
            if "total_cases" not in merged.columns:
                merged["total_cases"] = merged.get("backlog_cases", 0) * 2

        merged["court_short"] = merged["court"].apply(shorten_court_name)
        merged = merged.sort_values("backlog_cases", ascending=False)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔴 Highest Backlog", merged.iloc[0]["court"] if len(merged) else "N/A",
                      delta=f"{int(merged.iloc[0]['backlog_cases'])} cases" if len(merged) else "")
        with col2:
            total_backlog = int(merged["backlog_cases"].sum())
            st.metric("📊 Total Pending Cases", f"{total_backlog:,}")

        st.markdown("#### Backlog by Court")
        fig = px.bar(merged, x="court_short", y="backlog_cases", color="backlog_cases",
                     color_continuous_scale="Reds", labels={"backlog_cases": "Pending Cases", "court_short": "Court"})
        fig.update_layout(xaxis_tickangle=-35, height=420, margin=dict(b=120))
        st.plotly_chart(fig, use_container_width=True)

        if "backlog_rate" in merged.columns:
            st.markdown("#### Backlog Rate Heatmap")
            merged_sorted = merged.sort_values("backlog_rate", ascending=False)
            fig2 = go.Figure(go.Bar(
                x=merged_sorted["court_short"],
                y=merged_sorted["backlog_rate"],
                marker=dict(color=merged_sorted["backlog_rate"], colorscale="YlOrRd"),
            ))
            fig2.update_layout(title="Backlog Rate (%)", height=380, xaxis_tickangle=-35, margin=dict(b=120))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### Detailed Backlog Table")
        display_cols = [c for c in ["court", "backlog_cases", "backlog_rate", "total_cases"] if c in merged.columns]
        st.dataframe(merged[display_cols].rename(columns={
            "court": "Court", "backlog_cases": "Pending Cases",
            "backlog_rate": "Backlog Rate (%)", "total_cases": "Total Cases",
        }), use_container_width=True)
    else:
        st.info("No backlog data available.")

# ---------------------------------------------------------------------------
# Page: Model Performance
# ---------------------------------------------------------------------------

elif page == "🤖 Model Performance":
    st.markdown('<h1 class="main-header">🤖 Model Performance</h1>', unsafe_allow_html=True)
    st.markdown("Evaluation metrics for duration and outcome prediction models.")

    retrain_col, _ = st.columns([1, 3])
    with retrain_col:
        if st.button("🔄 Retrain Models"):
            with st.spinner("Retraining models…"):
                result, is_mock = call_backend("GET", "/models/retrain")
                if is_mock or not result:
                    st.warning("Backend unavailable. Could not retrain.")
                else:
                    st.success("Models retrained successfully!")
                    metrics = result.get("metrics", {})
                    st.json(metrics)

    st.markdown("---")
    metrics = mock_model_metrics()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⏱ Duration Prediction Model")
        dur = metrics["duration_model"]
        st.metric("Model Type", dur.get("model", "XGBoost"))
        m1, m2, m3 = st.columns(3)
        m1.metric("MAE (days)", dur.get("MAE", "N/A"))
        m2.metric("RMSE (days)", dur.get("RMSE", "N/A"))
        m3.metric("R² Score", dur.get("R2", "N/A"))

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=dur.get("R2", 0) * 100,
            title={"text": "R² (%)"},
            gauge={"axis": {"range": [0, 100]},
                   "bar": {"color": "#1565c0"},
                   "steps": [{"range": [0, 50], "color": "#ef9a9a"}, {"range": [50, 70], "color": "#fff176"}, {"range": [70, 100], "color": "#a5d6a7"}]},
        ))
        fig.update_layout(height=260, margin=dict(t=40, b=10, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🎯 Outcome Prediction Model")
        out = metrics["outcome_model"]
        m1, m2 = st.columns(2)
        m1.metric("Accuracy", f"{out.get('accuracy', 0) * 100:.1f}%")
        m2.metric("Weighted F1", f"{out.get('weighted_f1', 0) * 100:.1f}%")

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=out.get("accuracy", 0) * 100,
            title={"text": "Accuracy (%)"},
            gauge={"axis": {"range": [0, 100]},
                   "bar": {"color": "#2e7d32"},
                   "steps": [{"range": [0, 60], "color": "#ef9a9a"}, {"range": [60, 80], "color": "#fff176"}, {"range": [80, 100], "color": "#a5d6a7"}]},
        ))
        fig.update_layout(height=260, margin=dict(t=40, b=10, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📌 Model Architecture")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Duration Prediction Pipeline**
- Features: Case Type, Court, Judge, Act, No. of Hearings
- Preprocessing: Label Encoding
- Models: XGBoost Regressor, Random Forest (best selected)
- Explanation: SHAP TreeExplainer
        """)
    with col2:
        st.markdown("""
**Outcome Prediction Pipeline**
- Features: Case Type, Court, Judge, Act, No. of Hearings
- Preprocessing: Label Encoding
- Model: XGBoost Classifier
- Explanation: Feature Importances / SHAP
        """)

    st.markdown("### 🔍 Semantic Search")
    st.markdown("""
- **Model:** `all-MiniLM-L6-v2` (Sentence Transformers)
- **Index:** FAISS Inner Product (cosine similarity)
- **Use Case:** Find precedent cases similar to a query judgment
    """)
