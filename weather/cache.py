import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .models import PointMetadata


class WeatherCache:
    def __init__(self, db_path: str, ttl_minutes: int = 15):
        self.db_path = Path(db_path)
        self.ttl_minutes = ttl_minutes
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS points_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS forecast_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _is_fresh(self, created_at: str) -> bool:
        created = datetime.fromisoformat(created_at)
        return datetime.now(timezone.utc) - created <= timedelta(minutes=self.ttl_minutes)

    def _read_row(self, table: str, key: str) -> Optional[tuple[str, str]]:
        conn = self._connect()
        try:
            row = conn.execute(
                f"SELECT value, created_at FROM {table} WHERE key = ?",
                (key,),
            ).fetchone()
        finally:
            conn.close()
        return row if row else None

    def _write_row(self, table: str, key: str, payload: dict) -> None:
        conn = self._connect()
        try:
            conn.execute(
                f"INSERT OR REPLACE INTO {table}(key, value, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(payload), datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_point(self, latitude: float, longitude: float) -> Optional[PointMetadata]:
        key = f"{latitude:.4f},{longitude:.4f}"
        row = self._read_row("points_cache", key)
        if not row:
            return None

        payload, created = row
        if not self._is_fresh(created):
            return None

        data = json.loads(payload)
        return PointMetadata(**data)

    def set_point(self, point: PointMetadata) -> None:
        key = f"{point.latitude:.4f},{point.longitude:.4f}"
        self._write_row("points_cache", key, point.__dict__)

    def get_forecast(self, key: str, allow_stale: bool = False) -> Optional[dict]:
        row = self._read_row("forecast_cache", key)
        if not row:
            return None

        payload, created = row
        if not allow_stale and not self._is_fresh(created):
            return None
        data = json.loads(payload)
        data["_cache_fresh"] = self._is_fresh(created)
        return data

    def set_forecast(self, key: str, payload: dict) -> None:
        self._write_row("forecast_cache", key, payload)
