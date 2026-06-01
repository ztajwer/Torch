from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import build_router
from app.config import settings
from app.logging import setup_logging
from app.pipeline.orchestrator import PipelineOrchestrator
from app.scrapers.registry import default_marketplaces
from app.storage.json_store import JsonStore


def create_app() -> FastAPI:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(settings.data_dir / "torch.log")

    log = logging.getLogger("torch")
    log.info("starting %s env=%s data_dir=%s", settings.app_name, settings.environment, settings.data_dir)

    store = JsonStore(settings.data_dir)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not store.read_marketplaces():
            store.write_marketplaces(default_marketplaces())
        if len(store.read_products()) == 0:
            log.info("catalog empty — scheduling initial scrape")
            asyncio.create_task(PipelineOrchestrator(store).run_full_pipeline())
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    origins = _parse_cors_origins(settings.cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials="*" not in origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(build_router(store))

    @app.get("/health")
    def health():
        return {"status": "ok", "environment": settings.environment}

    static_dir = Path(__file__).resolve().parent.parent / "static"
    if settings.serve_static and static_dir.is_dir():
        log.info("serving frontend from %s", static_dir)
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return app


def _parse_cors_origins(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text or text == "*":
        return ["*"]
    return [o.strip() for o in text.split(",") if o.strip()]


app = create_app()

