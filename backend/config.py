from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration loaded from environment and .env file.
    """
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    BACKEND_DIR: Path = Path(__file__).resolve().parent
    DATASETS_DIR: Path = BASE_DIR / "datasets"

    # API Keys
    GOOGLE_API_KEY: str = Field(..., description="Google Gemini API Key")
    GEMINI_API_KEY: str = Field(default="", description="Optional alias for Google API Key")

    # LLM Settings
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model identifier")
    GEMINI_TEMPERATURE: float = Field(default=0.1, description="Sampling temperature")
    GEMINI_API_VERSION: str = Field(default="v1beta", description="API version for fast thinking control")
    GEMINI_THINKING_BUDGET: int = Field(default=0, description="0 turns off thinking tokens for fast response")

    # Embeddings & Vector Store Settings
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Local HuggingFace embedding model"
    )
    CHROMA_PERSIST_DIR: Path = BACKEND_DIR / "chroma_db"
    FAQ_COLLECTION_NAME: str = Field(default="faq_collection", description="ChromaDB collection for FAQs")

    # SQLite Database
    SQLITE_DB_PATH: Path = BACKEND_DIR / "db.sqlite"

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Centralized singleton instance
settings = Settings()
