"""Read-only probe: how many ARCHIVE (currently-unlinked) labor violations are
actually listed companies that were missed only due to spelling differences
(臺/台, bracketed 負責人, legal-entity suffix, abbreviation)?

This estimates the "recall" upside that 5b's v2 rule does NOT capture on its own
(v2 only fixes/​prevents mis-links; it does not normalise names). It tells us
whether a normalisation/​fuzzy step (D4-ish) is worth adding. Safe (mode=ro).
"""

import re
import sqlite3
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
MAIN_DB = BACKEND / "bossy_radar.db"
ARCHIVE_DB = BACKEND / "archive.db"

BRACKET = re.compile(r"[（(][^（）()]*[）)]")
SUFFIXES = ("股份有限公司", "有限公司", "股份公司")


def normalize(s: str) -> str:
    if not s:
        return ""
    s = BRACKET.sub("", s.strip())  # drop (負責人) annotations
    s = s.replace("臺", "台")  # 臺/台 unification
    for suf in SUFFIXES:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    return s.strip()


def main():
    main_conn = sqlite3.connect(f"file:{MAIN_DB.as_posix()}?mode=ro", uri=True)
    arch_conn = sqlite3.connect(f"file:{ARCHIVE_DB.as_posix()}?mode=ro", uri=True)

    # Build normalized index over company master (name + abbreviation).
    norm_map = {}
    for code, name, abbr in main_conn.execute(
        "SELECT code, name, abbreviation FROM company"
    ).fetchall():
        for raw in (name, abbr):
            key = normalize(raw or "")
            if key:
                norm_map.setdefault(key, code)

    # exact-name set (already-linkable today) to separate "spelling-only" misses.
    exact_names = set()
    for (name,) in main_conn.execute("SELECT name FROM company").fetchall():
        exact_names.add((name or "").strip())

    rows = arch_conn.execute(
        "SELECT company_name, COUNT(*) FROM violation GROUP BY company_name"
    ).fetchall()

    recall_names = recall_rows = 0
    arch_total = 0
    samples = []
    for name, n in rows:
        arch_total += n
        nm = (name or "").strip()
        key = normalize(nm)
        if key and key in norm_map:
            recall_names += 1
            recall_rows += n
            if len(samples) < 30:
                samples.append((n, nm, norm_map[key]))

    print(f"archive 勞動違規總筆數: {arch_total}")
    print("正規化後可命中上市櫃主檔 (潛在漏接可救回):")
    print(f"  unique 公司名 = {recall_names}")
    print(
        f"  違規筆數      = {recall_rows}  ({recall_rows * 100 / arch_total:.1f}% of archive)"
    )
    print(f"\n抽樣 (依筆數排序, 前 {min(30, len(samples))}):")
    print("  [筆數] archive 原始名稱  ->  正規化後命中 code")
    for n, nm, code in sorted(samples, key=lambda x: -x[0]):
        print(f"  [{n}] {nm}  ->  {code}")

    main_conn.close()
    arch_conn.close()


if __name__ == "__main__":
    main()
