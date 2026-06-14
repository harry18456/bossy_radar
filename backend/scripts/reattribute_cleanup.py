"""Re-attribution cleanup (change 5b).

A resync uses upsert (ON CONFLICT DO UPDATE) and never deletes, so an existing
main-DB mis-link is NOT removed by re-syncing: the new match for e.g. a bare
personal name routes that row to archive but leaves the stale main row intact.
This script fixes that. For every linked row in the main DB it recomputes
attribution with the real CompanyMatcher:

  - new result equals current  -> leave as is
  - new result is None         -> move the row to archive (unlinked), delete from main
  - new result differs         -> update company_code in place

Idempotent. Dry-run by default; pass --apply to write. Back up the DBs first.

Usage:
  uv run python scripts/reattribute_cleanup.py            # dry-run (report only)
  uv run python scripts/reattribute_cleanup.py --apply    # write changes
"""

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from sqlmodel import Session, select  # noqa: E402

from app.db.session import archive_engine, engine  # noqa: E402
from app.models.environmental_violation import EnvironmentalViolation  # noqa: E402
from app.models.violation import Violation  # noqa: E402
from app.services.company_matcher import CompanyMatcher  # noqa: E402
from app.services.db_upsert import model_values, upsert_on_conflict  # noqa: E402

APPLY = "--apply" in sys.argv


def cleanup(label, model, match_fn):
    with Session(engine) as s:
        matcher = CompanyMatcher(s)
    moved = updated = kept = 0
    with Session(engine) as main, Session(archive_engine) as arch:
        rows = main.exec(select(model).where(model.company_code.is_not(None))).all()
        for r in rows:
            new = match_fn(matcher, r)
            if new == r.company_code:
                kept += 1
            elif new is None:
                moved += 1
                if APPLY:
                    r.company_code = None
                    upsert_on_conflict(
                        arch,
                        model,
                        model_values(r),
                        conflict_cols=("dedup_key",),
                        no_update=("id", "created_at", "dedup_key"),
                    )
                    main.delete(r)
            else:
                updated += 1
                if APPLY:
                    r.company_code = new
        if APPLY:
            main.commit()
            arch.commit()
    print(f"[{label}] kept={kept} moved_to_archive={moved} relinked={updated}")
    return moved, updated


def main():
    mode = "APPLY (writing)" if APPLY else "DRY-RUN (no writes)"
    print(f"=== Re-attribution cleanup — {mode} ===")
    cleanup("violation", Violation, lambda m, r: m.match(company_name=r.company_name))
    cleanup(
        "environmental",
        EnvironmentalViolation,
        lambda m, r: m.match(tax_id=r.tax_id, company_name=r.company_name),
    )


if __name__ == "__main__":
    main()
