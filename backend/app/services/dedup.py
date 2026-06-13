"""Deterministic dedup keys for violations (BACKEND_AUDIT H5).

A violation/environmental-violation whose disposition number is empty or null
has no natural unique key, so it was re-inserted on every sync. These functions
derive a stable synthetic key from the identifying fields instead. The SAME
rules MUST be used by the application upsert and by the migration backfill so
existing rows and freshly synced rows collapse to one key.
"""

import hashlib
from datetime import date


def _date_part(value: date | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _synthetic(parts: list) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:32]
    return f"syn:{digest}"


def violation_dedup_key(
    data_source: str,
    disposition_no: str | None,
    company_name: str | None,
    penalty_date: date | str | None,
    law_article: str | None,
    fine_amount: int | None,
) -> str:
    """Natural key when disposition_no is present, else a deterministic hash."""
    disposition = (disposition_no or "").strip()
    if disposition:
        return f"{data_source}|{disposition}"
    return _synthetic(
        [
            company_name,
            _date_part(penalty_date),
            law_article,
            fine_amount,
            data_source,
        ]
    )


def env_violation_dedup_key(
    disposition_no: str | None,
    company_name: str | None,
    penalty_date: date | str | None,
    violation_reason: str | None,
    fine_amount: int | None,
) -> str:
    """Disposition number when present, else a deterministic hash."""
    disposition = (disposition_no or "").strip()
    if disposition:
        return disposition
    return _synthetic(
        [
            company_name,
            _date_part(penalty_date),
            violation_reason,
            fine_amount,
        ]
    )
