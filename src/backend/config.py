from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and `.env`."""

    openai_api_key: str | None = None
    openai_model: str | None = None
    reasoning_effort: str | None = None
    #: Comma-separated origins the browser frontend may call from. Set this
    #: when demoing from a phone or another host, otherwise CORS blocks it.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_liste(self) -> list[str]:
        return [teil.strip() for teil in self.cors_origins.split(",") if teil.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
