"""unique constraints and dedup keys

Adds dedup_key to violation/environmentalviolation, backfills it with the same
rules as app/services/dedup.py, and adds UNIQUE constraints on every table's
natural key so idempotency is enforced by the database (BACKEND_AUDIT H5/H6).

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.services.dedup import env_violation_dedup_key, violation_dedup_key

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MOPS_TABLES = [
    "non_manager_salary",
    "employee_benefit",
    "welfare_policy",
    "salary_adjustment",
]


def _backfill_violation(conn) -> None:
    # Fast path: every row with a real disposition number (all existing rows).
    conn.execute(
        sa.text(
            "UPDATE violation SET dedup_key = data_source || '|' || trim(disposition_no) "
            "WHERE disposition_no IS NOT NULL AND trim(disposition_no) != ''"
        )
    )
    # Empty/null disposition numbers need the synthetic hash (matches dedup.py).
    rows = conn.execute(
        sa.text(
            "SELECT id, data_source, disposition_no, company_name, penalty_date, "
            "law_article, fine_amount FROM violation WHERE dedup_key IS NULL"
        )
    ).fetchall()
    for r in rows:
        key = violation_dedup_key(
            data_source=r.data_source,
            disposition_no=r.disposition_no,
            company_name=r.company_name,
            penalty_date=r.penalty_date,
            law_article=r.law_article,
            fine_amount=r.fine_amount,
        )
        conn.execute(
            sa.text("UPDATE violation SET dedup_key = :k WHERE id = :id"),
            {"k": key, "id": r.id},
        )


def _backfill_env(conn) -> None:
    conn.execute(
        sa.text(
            "UPDATE environmentalviolation SET dedup_key = trim(disposition_no) "
            "WHERE disposition_no IS NOT NULL AND trim(disposition_no) != ''"
        )
    )
    rows = conn.execute(
        sa.text(
            "SELECT id, disposition_no, company_name, penalty_date, violation_reason, "
            "fine_amount FROM environmentalviolation WHERE dedup_key IS NULL"
        )
    ).fetchall()
    for r in rows:
        key = env_violation_dedup_key(
            disposition_no=r.disposition_no,
            company_name=r.company_name,
            penalty_date=r.penalty_date,
            violation_reason=r.violation_reason,
            fine_amount=r.fine_amount,
        )
        conn.execute(
            sa.text("UPDATE environmentalviolation SET dedup_key = :k WHERE id = :id"),
            {"k": key, "id": r.id},
        )


def upgrade() -> None:
    conn = op.get_bind()

    with op.batch_alter_table("violation", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("dedup_key", sa.String(), nullable=True))
        batch_op.create_index("ix_violation_dedup_key", ["dedup_key"])
        batch_op.create_unique_constraint("uq_violation_dedup_key", ["dedup_key"])
    _backfill_violation(conn)

    with op.batch_alter_table("environmentalviolation", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("dedup_key", sa.String(), nullable=True))
        batch_op.create_index("ix_environmentalviolation_dedup_key", ["dedup_key"])
        batch_op.create_unique_constraint(
            "uq_environmentalviolation_dedup_key", ["dedup_key"]
        )
    _backfill_env(conn)

    for table in MOPS_TABLES:
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.create_unique_constraint(
                f"uq_{table}_natural",
                ["raw_company_code", "year", "market_type"],
            )


def downgrade() -> None:
    for table in MOPS_TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(f"uq_{table}_natural", type_="unique")

    with op.batch_alter_table("environmentalviolation") as batch_op:
        batch_op.drop_constraint("uq_environmentalviolation_dedup_key", type_="unique")
        batch_op.drop_index("ix_environmentalviolation_dedup_key")
        batch_op.drop_column("dedup_key")

    with op.batch_alter_table("violation") as batch_op:
        batch_op.drop_constraint("uq_violation_dedup_key", type_="unique")
        batch_op.drop_index("ix_violation_dedup_key")
        batch_op.drop_column("dedup_key")
