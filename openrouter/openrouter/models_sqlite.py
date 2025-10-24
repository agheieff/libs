from __future__ import annotations
import json
import re
import sqlite3
from typing import Callable, Optional, Union

from .models import ModelSpec, Catalog, get_default_catalog, validate_catalog


def _assert_safe_table(name: str) -> None:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise ValueError("Invalid table name; use alphanumerics and underscores, not starting with a digit")


def create_table_sql(table: str = "models") -> str:
    _assert_safe_table(table)
    return (
        f'CREATE TABLE IF NOT EXISTS "{table}" ('
        ' id TEXT PRIMARY KEY,'
        ' provider TEXT NOT NULL,'
        ' label TEXT NOT NULL,'
        ' family TEXT NOT NULL,'
        ' context_window INTEGER NOT NULL,'
        ' max_output_tokens INTEGER NOT NULL,'
        ' modalities TEXT NOT NULL,'
        ' features TEXT NOT NULL,'
        ' tiers TEXT NOT NULL,'
        ' pricing TEXT,'
        ' limits TEXT,'
        ' meta TEXT'
        ')'
    )


def ensure_sqlite_schema(conn_or_path: Union[str, sqlite3.Connection], table: str = "models") -> sqlite3.Connection:
    _assert_safe_table(table)
    conn = sqlite3.connect(conn_or_path) if isinstance(conn_or_path, str) else conn_or_path
    conn.execute(create_table_sql(table))
    conn.commit()
    return conn


def sqlite_upserter(
    conn_or_path: Union[str, sqlite3.Connection],
    *,
    table: str = "models",
    autocommit: bool = True,
) -> Callable[[ModelSpec], None]:
    conn = ensure_sqlite_schema(conn_or_path, table)
    _assert_safe_table(table)
    sql = (
        f'INSERT INTO "{table}" (id, provider, label, family, context_window, max_output_tokens,'
        ' modalities, features, tiers, pricing, limits, meta)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        ' ON CONFLICT(id) DO UPDATE SET'
        '  provider=excluded.provider,'
        '  label=excluded.label,'
        '  family=excluded.family,'
        '  context_window=excluded.context_window,'
        '  max_output_tokens=excluded.max_output_tokens,'
        '  modalities=excluded.modalities,'
        '  features=excluded.features,'
        '  tiers=excluded.tiers,'
        '  pricing=excluded.pricing,'
        '  limits=excluded.limits,'
        '  meta=excluded.meta'
    )

    def _upsert(spec: ModelSpec) -> None:
        payload = (
            spec["id"],
            spec.get("provider", "unknown"),
            spec.get("label", spec["id"]),
            spec.get("family", "unknown"),
            int(spec.get("context_window", 128000)),
            int(spec.get("max_output_tokens", 8192)),
            json.dumps(spec.get("modalities", {}), ensure_ascii=False),
            json.dumps(spec.get("features", {}), ensure_ascii=False),
            json.dumps(spec.get("tiers", {}), ensure_ascii=False),
            json.dumps(spec.get("pricing", {}), ensure_ascii=False),
            json.dumps(spec.get("limits", {}), ensure_ascii=False),
            json.dumps(spec.get("meta", {}), ensure_ascii=False),
        )
        conn.execute(sql, payload)
        if autocommit:
            conn.commit()

    return _upsert


def seed_sqlite(
    conn_or_path: Union[str, sqlite3.Connection],
    *,
    table: str = "models",
    cat: Optional[Catalog] = None,
) -> int:
    conn = ensure_sqlite_schema(conn_or_path, table)
    data = cat or get_default_catalog()
    validate_catalog(data)
    upsert = sqlite_upserter(conn, table=table, autocommit=False)
    for m in data:
        upsert(m)
    conn.commit()
    return len(data)
