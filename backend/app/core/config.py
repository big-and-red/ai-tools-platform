import os

from pydantic import computed_field
from pydantic_settings import BaseSettings

STAND_FILE_MAP = {
    "local": "envs/local/local.env",
    "dev": "envs/dev/dev.env",
    "test": "envs/test/test.env",
    "prod": "envs/prod/prod.env",
}
DEFAULT_STAND = "local"


class Settings(BaseSettings):
    STAND_NAME: str = DEFAULT_STAND

    PG_DRIVER: str = "asyncpg"
    PG_USERNAME: str
    PG_PASSWORD: str
    PG_HOST: str
    PG_PORT: str = "5432"
    PG_DATABASE: str

    REDIS_URL: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    LANGFUSE_ENABLED: bool = False
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"

    STRIPE_ENABLED: bool = False
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    TAVILY_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"

    # Credits
    CREDIT_RATE: float = 1000.0
    CREDIT_MARKUP: float = 3.0
    TAVILY_ADVANCED_COST_USD: float = 0.01

    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+{self.PG_DRIVER}://{self.PG_USERNAME}:"
            f"{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.PG_USERNAME}:"
            f"{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def PG_DSN(self) -> str:
        """Plain psycopg3 DSN for langgraph-checkpoint-postgres (no SQLAlchemy prefix)."""
        return (
            f"postgresql://{self.PG_USERNAME}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
        )

    model_config = {
        "extra": "ignore",
        "env_file": STAND_FILE_MAP.get(
            os.getenv("STAND_NAME", DEFAULT_STAND), STAND_FILE_MAP[DEFAULT_STAND]
        ),
    }


settings = Settings()
