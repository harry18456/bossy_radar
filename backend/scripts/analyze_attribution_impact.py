"""Dry-run attribution impact using the REAL CompanyMatcher (change 5b).

Applies the production matcher to a DB snapshot (latest backup by default) and
reports how company attribution shifts versus the linkage currently stored.
This runs the SAME code the live ETL uses — no parallel re-implementation — so
the numbers predict the post-resync state.

Read-only: row reads use SQLite mode=ro; the matcher only SELECTs the company
table (it never writes). Pass explicit paths to analyze the live DBs instead of
the backup.

Usage:
  uv run python scripts/analyze_attribution_impact.py [MAIN_DB ARCHIVE_DB]
"""

import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from sqlmodel import Session, create_engine  # noqa: E402

from app.services.company_matcher import CompanyMatcher  # noqa: E402


def latest_backup() -> tuple[Path, Path]:
    bdir = BACKEND / "db_backups"
    dirs = sorted(p for p in bdir.glob("*") if p.is_dir()) if bdir.exists() else []
    if dirs:
        return dirs[-1] / "bossy_radar.db", dirs[-1] / "archive.db"
    return BACKEND / "bossy_radar.db", BACKEND / "archive.db"


def ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)


def build_matcher(main_db: Path) -> CompanyMatcher:
    """Load the company index via the real matcher (SELECT only, no writes)."""
    engine = create_engine(f"sqlite:///{main_db.as_posix()}")
    with Session(engine) as s:
        matcher = CompanyMatcher(s)
    engine.dispose()
    return matcher


def mops_tables(conn: sqlite3.Connection) -> list[str]:
    out = []
    for (t,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall():
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{t}')").fetchall()]
        if "raw_company_code" in cols and "company_code" in cols:
            out.append(t)
    return out


def main() -> None:
    if len(sys.argv) >= 3:
        main_db, arch_db = Path(sys.argv[1]), Path(sys.argv[2])
    else:
        main_db, arch_db = latest_backup()
    print(f"main_db    = {main_db}")
    print(f"archive_db = {arch_db}\n")

    matcher = build_matcher(main_db)
    print(
        f"companies={len(matcher.code_set)} "
        f"tax_id={len(matcher.tax_id_map)} names={len(matcher.name_map)}\n"
    )

    mc, ac = ro(main_db), ro(arch_db)

    # ---- Labor ----
    lab = defaultdict(int)
    drop_samples = []
    for name, cur, n in mc.execute(
        "SELECT company_name, company_code, COUNT(*) "
        "FROM violation GROUP BY company_name, company_code"
    ).fetchall():
        new = matcher.match(company_name=name)
        if new == cur:
            lab["keep"] += n
        elif new is not None:
            lab["relink"] += n
        else:
            lab["drop"] += n
            if len(drop_samples) < 30:
                drop_samples.append((n, name, cur))
    for name, n in ac.execute(
        "SELECT company_name, COUNT(*) FROM violation GROUP BY company_name"
    ).fetchall():
        if matcher.match(company_name=name) is not None:
            lab["rescue"] += n

    print("=== 勞動違規 Violation (real matcher vs 現況) ===")
    print(
        f"  保持={lab['keep']}  改連別家={lab['relink']}  "
        f"連結→archive={lab['drop']}  archive→救回={lab['rescue']}"
    )
    print("  連結→archive 抽樣 (應為純人名):")
    for n, name, cur in sorted(drop_samples, key=lambda x: -x[0])[:15]:
        print(f"    [{n}] 『{name}』 現連 {cur}")

    # ---- Env ----
    env = defaultdict(int)
    env_drop = []
    for name, cur, tax_id, n in mc.execute(
        "SELECT company_name, company_code, tax_id, COUNT(*) "
        "FROM environmentalviolation GROUP BY company_name, company_code, tax_id"
    ).fetchall():
        new = matcher.match(tax_id=tax_id, company_name=name)
        if new == cur:
            env["keep"] += n
        elif new is not None:
            env["relink"] += n
        else:
            env["drop"] += n
            if len(env_drop) < 10:
                env_drop.append((n, name, tax_id, cur))
    print("\n=== 環境違規 EnvironmentalViolation ===")
    print(f"  保持={env['keep']}  改連別家={env['relink']}  連結→archive={env['drop']}")
    for n, name, tax_id, cur in env_drop:
        print(f"    [{n}] 『{name}』 tax_id={tax_id} 現連 {cur}")

    # ---- MOPS ----
    mt = mops_tables(mc)
    mops = defaultdict(int)
    for t in mt:
        for name, raw, cur, n in mc.execute(
            f"SELECT company_name, raw_company_code, company_code, COUNT(*) "
            f"FROM {t} GROUP BY company_name, raw_company_code, company_code"
        ).fetchall():
            new = matcher.match(company_code=raw, company_name=name)
            if new == cur:
                mops["keep"] += n
            elif new is not None:
                mops["relink"] += n
            else:
                mops["drop"] += n
    print(f"\n=== MOPS {mt} ===")
    print(
        f"  保持={mops['keep']}  改連別家={mops['relink']}  連結→archive={mops['drop']}"
    )

    mc.close()
    ac.close()


if __name__ == "__main__":
    main()
