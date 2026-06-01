from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TORCH_",
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TORCH"
    environment: str = "dev"

    # Comma-separated origins, or * for any (dev only)
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    # Serve frontend/dist copied to backend/static (production Docker / Render)
    serve_static: bool = False

    # Storage lives at repo-root/data by default
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"

    # Lightweight scrape limits (tune per site)
    http_timeout_s: float = 20.0
    max_retries: int = 3
    rate_limit_rps: float = 2.5
    search_rate_limit_rps: float = 6.0
    max_pages_per_source: int = 12
    max_pages_per_search: int = 3
    search_timeout_s: float = 35.0

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"


settings = Settings()

