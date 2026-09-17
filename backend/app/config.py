"""Application configuration via Pydantic Settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "app"
    postgres_password: str = "changeme"
    postgres_db: str = "loganalyzer"

    # AI Gateway
    ai_gateway_url: str = "http://localhost:10000"

    # Embedding
    embedding_model: str = "intfloat/multilingual-e5-small"

    # Security
    api_key_secret: str = "changeme"
    api_key_header: str = "X-API-Key"

    # Rate Limiting
    rate_limit_chat_per_min: int = 10

    # Processing
    chunk_size_lines: int = 50
    chunk_overlap_lines: int = 10
    vector_similarity_threshold: float = 0.7
    max_file_size_mb: int = 100

    # App
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    @property
    def database_url(self) -> str:
        """Build async database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
