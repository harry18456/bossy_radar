"""DB-enforced idempotent upsert via SQLite ON CONFLICT (BACKEND_AUDIT H5/H6).

Replaces the fragile SELECT-then-INSERT pattern: a row whose natural key (or
dedup key) already exists is updated in a single statement, so concurrent or
retried syncs cannot create duplicates. Build `values` from a model instance so
SQLModel's defaults (created_at/last_updated) are populated — a raw insert does
NOT run Python-side defaults.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session


def model_values(instance) -> dict[str, Any]:
    """All column values of a model instance except the autoincrement id."""
    return {
        col.name: getattr(instance, col.name)
        for col in type(instance).__table__.columns
        if col.name != "id"
    }


def upsert_on_conflict(
    session: Session,
    model: type,
    values: Mapping[str, Any],
    conflict_cols: Iterable[str],
    no_update: Iterable[str] = ("id", "created_at"),
) -> None:
    conflict = list(conflict_cols)
    no_update_set = set(no_update) | set(conflict)
    stmt = sqlite_insert(model).values(**values)
    update = {k: stmt.excluded[k] for k in values if k not in no_update_set}
    stmt = stmt.on_conflict_do_update(index_elements=conflict, set_=update)
    session.execute(stmt)
