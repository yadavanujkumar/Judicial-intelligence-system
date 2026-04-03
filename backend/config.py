from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://judicial:judicial123@localhost:5432/judicial_db"
    SECRET_KEY: str = "judicial-intelligence-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FAISS_INDEX_PATH: str = "models/faiss_index"
    DURATION_MODEL_PATH: str = "models/duration_model.joblib"
    OUTCOME_MODEL_PATH: str = "models/outcome_model.joblib"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"


settings = Settings()
