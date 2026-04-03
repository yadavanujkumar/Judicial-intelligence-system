from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(100), primary_key=True, index=True)
    court = Column(String(200), nullable=False)
    case_type = Column(String(50), nullable=False)
    filing_date = Column(DateTime, nullable=False)
    decision_date = Column(DateTime, nullable=True)
    duration_days = Column(Integer, nullable=True)
    judge = Column(String(200), nullable=True)
    petitioner = Column(String(300), nullable=True)
    respondent = Column(String(300), nullable=True)
    act = Column(String(300), nullable=True)
    outcome = Column(String(100), nullable=True)
    num_hearings = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    judgments = relationship("Judgment", back_populates="case", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="case", cascade="all, delete-orphan")


class Judgment(Base):
    __tablename__ = "judgments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(100), ForeignKey("cases.case_id"), nullable=False)
    judgment_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    embedding_json = Column(Text, nullable=True)

    case = relationship("Case", back_populates="judgments")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(100), ForeignKey("cases.case_id"), nullable=True)
    predicted_duration = Column(Float, nullable=True)
    predicted_outcome = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="predictions")


class AnalyticsRecord(Base):
    __tablename__ = "analytics_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    court = Column(String(200), nullable=False)
    avg_duration = Column(Float, nullable=True)
    total_cases = Column(Integer, default=0)
    pending_cases = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
