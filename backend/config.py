from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Databases
    patient_db_url: str = "postgresql+psycopg2://admin:secretpass@localhost:5432/patient_db"
    appointment_db_url: str = "postgresql+psycopg2://admin:secretpass@localhost:5432/appointment_db"
    prescription_db_url: str = "postgresql+psycopg2://admin:secretpass@localhost:5432/prescription_db"
    analytics_db_url: str = "postgresql+psycopg2://admin:secretpass@localhost:5432/analytics_db"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "medical_knowledge"

    # Auth
    secret_key: str = "change-me-to-a-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Telegram
    telegram_bot_token: str = ""

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    # Whisper
    whisper_api_url: str = "https://api.groq.com/openai/v1/audio/transcriptions"

    # App
    app_env: str = "development"
    log_level: str = "INFO"


settings = Settings()
