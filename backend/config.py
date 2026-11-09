from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_prompt_file(file_path: Path) -> str:
    """Helper to safely read prompt text from file."""
    if file_path.exists():
        return file_path.read_text(encoding="utf-8").strip()
    return ""


class Settings(BaseSettings):
    """
    Centralized application configuration loaded from environment, .env file,
    and external prompt templates. Single source of truth for all paths and parameters.
    """
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    BACKEND_DIR: Path = Path(__file__).resolve().parent
    DATASETS_DIR: Path = BASE_DIR / "datasets"
    PROMPTS_DIR: Path = BASE_DIR / "prompts"
    DATABASE_DIR: Path = BASE_DIR / "database"

    # Datasets paths
    FAQ_DATA_PATH: Path = DATASETS_DIR / "faq_data.csv"
    ECOMMERCE_DATA_PATH: Path = DATASETS_DIR / "ecommerce_data_final.csv"

    # Centralized Database paths (Inside root database/ directory)
    CHROMA_PERSIST_DIR: Path = DATABASE_DIR / "chroma"
    SQLITE_DIR: Path = DATABASE_DIR / "sqlite"
    SQLITE_DB_PATH: Path = SQLITE_DIR / "db.sqlite"
    FAQ_COLLECTION_NAME: str = Field(default="faq_collection", description="ChromaDB collection for FAQs")

    # Canonical Relational Schema
    PRODUCT_SCHEMA: str = (
        "Table: product\n"
        "Columns:\n"
        "- product_link: TEXT (hyperlink to product page on Flipkart)\n"
        "- title: TEXT (title of the product)\n"
        "- brand: TEXT (brand of product, e.g. Nike, Puma, Campus)\n"
        "- price: INTEGER (price in Indian Rupees)\n"
        "- discount: REAL (e.g., 0.10 for 10% off, 0.50 for 50% off)\n"
        "- avg_rating: REAL (rating from 0 to 5.0)\n"
        "- total_ratings: INTEGER (number of user reviews)"
    )

    # API Keys
    GOOGLE_API_KEY: str = Field(..., description="Google Gemini API Key")
    GEMINI_API_KEY: str = Field(default="", description="Optional alias for Google API Key")

    # LLM Settings
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite", description="Gemini model identifier")
    GEMINI_TEMPERATURE: float = Field(default=0.1, description="Sampling temperature")
    GEMINI_API_VERSION: str = Field(default="v1beta", description="API version for fast thinking control")
    GEMINI_THINKING_BUDGET: int = Field(default=0, description="0 turns off thinking tokens for fast response")

    # Embeddings & Vector Store Settings
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Local HuggingFace embedding model"
    )

    # Dynamic Prompts (Loaded from prompts/ folder)
    @property
    def FAQ_PROMPT(self) -> str:
        return _load_prompt_file(self.PROMPTS_DIR / "faq_prompt.txt")

    @property
    def SQL_GENERATION_PROMPT(self) -> str:
        return _load_prompt_file(self.PROMPTS_DIR / "sql_generation_prompt.txt")

    @property
    def SQL_SYNTHESIS_PROMPT(self) -> str:
        return _load_prompt_file(self.PROMPTS_DIR / "sql_synthesis_prompt.txt")

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Centralized singleton instance
settings = Settings()
