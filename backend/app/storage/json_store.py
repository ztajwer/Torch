from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
    with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def _read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        # Corruption guard: keep app alive; caller may rebuild.
        return default


@dataclass(frozen=True)
class JsonStore:
    root: Path

    @property
    def products_path(self) -> Path:
        return self.root / "products.json"

    @property
    def marketplaces_path(self) -> Path:
        return self.root / "marketplaces.json"

    @property
    def analytics_path(self) -> Path:
        return self.root / "analytics.json"

    @property
    def logs_path(self) -> Path:
        return self.root / "logs.json"

    def read_products(self) -> list[dict]:
        return _read_json(self.products_path, default=[])

    def write_products(self, products: list[dict]) -> None:
        _atomic_write_json(self.products_path, products)

    def read_marketplaces(self) -> list[dict]:
        return _read_json(self.marketplaces_path, default=[])

    def write_marketplaces(self, marketplaces: list[dict]) -> None:
        _atomic_write_json(self.marketplaces_path, marketplaces)

    def read_analytics(self) -> dict:
        return _read_json(self.analytics_path, default={})

    def write_analytics(self, analytics: dict) -> None:
        _atomic_write_json(self.analytics_path, analytics)

    def append_log_event(self, event: dict) -> None:
        # logs.json is a bounded append-only array (for easy UI consumption)
        existing = _read_json(self.logs_path, default=[])
        if not isinstance(existing, list):
            existing = []
        existing.append(event)
        # keep last 2000
        existing = existing[-2000:]
        _atomic_write_json(self.logs_path, existing)

    def read_logs(self) -> list[dict]:
        v = _read_json(self.logs_path, default=[])
        return v if isinstance(v, list) else []

    def upsert_products(
        self,
        new_products: Iterable[dict],
        *,
        key_field: str = "id",
    ) -> int:
        existing = self.read_products()
        by_id: dict[str, dict] = {}
        for p in existing:
            if isinstance(p, dict) and p.get(key_field):
                by_id[str(p[key_field])] = p
        written = 0
        for p in new_products:
            pid = str(p.get(key_field, ""))
            if not pid:
                continue
            prev = by_id.get(pid)
            if prev != p:
                by_id[pid] = p
                written += 1
        merged = list(by_id.values())
        _atomic_write_json(self.products_path, merged)
        return written

