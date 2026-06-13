"""baseline: snapshot of the pre-integrity schema

Captures the exact schema of the existing production databases (no dedup_key,
no UNIQUE constraints) so an already-populated database can be stamped at this
revision and only the post-baseline migrations execute against it.

Revision ID: 0001
Revises:
Create Date: 2026-06-13
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TABLES = [
    """CREATE TABLE company (
        name VARCHAR NOT NULL, abbreviation VARCHAR, market_type VARCHAR NOT NULL,
        industry VARCHAR, tax_id VARCHAR, chairman VARCHAR, manager VARCHAR,
        establishment_date DATE, listing_date DATE, capital INTEGER,
        address VARCHAR, website VARCHAR, email VARCHAR, stakeholder_url VARCHAR,
        governance_url VARCHAR, last_updated DATETIME NOT NULL, code VARCHAR NOT NULL,
        PRIMARY KEY (code))""",
    """CREATE TABLE violation (
        id INTEGER NOT NULL, company_code VARCHAR, company_name VARCHAR NOT NULL,
        data_source VARCHAR NOT NULL, authority VARCHAR, penalty_date DATE,
        announcement_date DATE, disposition_no VARCHAR, law_article VARCHAR,
        violation_content VARCHAR, fine_amount INTEGER NOT NULL,
        created_at DATETIME NOT NULL, last_updated DATETIME NOT NULL,
        PRIMARY KEY (id), FOREIGN KEY(company_code) REFERENCES company (code))""",
    """CREATE TABLE environmentalviolation (
        id INTEGER NOT NULL, company_code VARCHAR, tax_id VARCHAR, control_no VARCHAR,
        disposition_no VARCHAR, company_name VARCHAR NOT NULL, company_address VARCHAR,
        violation_address VARCHAR, violation_type VARCHAR, violation_date DATE,
        violation_reason VARCHAR, law_article VARCHAR, authority VARCHAR,
        penalty_date DATE, fine_amount INTEGER NOT NULL, penalty_reason VARCHAR,
        limit_date DATE, is_improved BOOLEAN, is_appeal BOOLEAN, appeal_result VARCHAR,
        is_paid BOOLEAN, illegal_profit INTEGER, other_penalty VARCHAR,
        is_serious BOOLEAN, created_at DATETIME NOT NULL, last_updated DATETIME NOT NULL,
        PRIMARY KEY (id), FOREIGN KEY(company_code) REFERENCES company (code))""",
    """CREATE TABLE non_manager_salary (
        id INTEGER NOT NULL, company_code VARCHAR, raw_company_code VARCHAR NOT NULL,
        company_name VARCHAR NOT NULL, year INTEGER NOT NULL, market_type VARCHAR NOT NULL,
        industry VARCHAR, employee_count INTEGER, total_salary INTEGER, avg_salary INTEGER,
        median_salary INTEGER, avg_salary_previous_year INTEGER, avg_salary_change FLOAT,
        median_salary_previous_year INTEGER, median_salary_change FLOAT,
        industry_avg_salary INTEGER, industry_median_salary INTEGER, eps FLOAT,
        industry_avg_eps FLOAT, is_avg_salary_under_500k VARCHAR,
        is_better_eps_lower_salary VARCHAR, is_eps_growth_salary_decrease VARCHAR,
        performance_salary_relation_note VARCHAR, improvement_measures_note VARCHAR,
        created_at DATETIME NOT NULL, last_updated DATETIME NOT NULL,
        PRIMARY KEY (id), FOREIGN KEY(company_code) REFERENCES company (code))""",
    """CREATE TABLE employee_benefit (
        id INTEGER NOT NULL, company_code VARCHAR, raw_company_code VARCHAR NOT NULL,
        company_name VARCHAR NOT NULL, year INTEGER NOT NULL, market_type VARCHAR NOT NULL,
        industry VARCHAR, company_category VARCHAR, employee_benefit_expense INTEGER,
        employee_salary_expense INTEGER, employee_count INTEGER,
        avg_benefit_per_employee INTEGER, avg_salary_current_year INTEGER,
        avg_salary_previous_year INTEGER, salary_change_rate FLOAT, eps FLOAT,
        industry_avg_benefit INTEGER, industry_avg_salary INTEGER, industry_avg_eps FLOAT,
        created_at DATETIME NOT NULL, last_updated DATETIME NOT NULL,
        PRIMARY KEY (id), FOREIGN KEY(company_code) REFERENCES company (code))""",
    """CREATE TABLE welfare_policy (
        id INTEGER NOT NULL, company_code VARCHAR, raw_company_code VARCHAR NOT NULL,
        company_name VARCHAR NOT NULL, year INTEGER NOT NULL, market_type VARCHAR NOT NULL,
        planned_salary_increase VARCHAR, planned_salary_increase_note VARCHAR,
        actual_salary_increase VARCHAR, actual_salary_increase_note VARCHAR,
        non_manager_salary_increase VARCHAR, non_manager_salary_increase_note VARCHAR,
        manager_salary_increase VARCHAR, manager_salary_increase_note VARCHAR,
        entry_salary_master VARCHAR, entry_salary_bachelor VARCHAR,
        entry_salary_highschool VARCHAR, entry_salary_note VARCHAR,
        created_at DATETIME NOT NULL, last_updated DATETIME NOT NULL,
        PRIMARY KEY (id), FOREIGN KEY(company_code) REFERENCES company (code))""",
    """CREATE TABLE salary_adjustment (
        id INTEGER NOT NULL, company_code VARCHAR, raw_company_code VARCHAR NOT NULL,
        company_name VARCHAR NOT NULL, year INTEGER NOT NULL, market_type VARCHAR NOT NULL,
        industry VARCHAR, pretax_net_profit INTEGER, allocation_ratio_min VARCHAR,
        allocation_ratio_max VARCHAR, board_resolution_date VARCHAR,
        actual_allocation_ratio VARCHAR, basic_employee_definition VARCHAR,
        basic_employee_count INTEGER, total_allocation_amount INTEGER,
        allocation_method VARCHAR, difference_amount VARCHAR, difference_reason VARCHAR,
        difference_handling VARCHAR, note VARCHAR, created_at DATETIME NOT NULL,
        last_updated DATETIME NOT NULL,
        PRIMARY KEY (id), FOREIGN KEY(company_code) REFERENCES company (code))""",
]

INDEXES = [
    "CREATE INDEX ix_company_market_type ON company (market_type)",
    "CREATE INDEX ix_company_tax_id ON company (tax_id)",
    "CREATE INDEX ix_company_name ON company (name)",
    "CREATE INDEX ix_violation_disposition_no ON violation (disposition_no)",
    "CREATE INDEX ix_violation_data_source ON violation (data_source)",
    "CREATE INDEX ix_violation_announcement_date ON violation (announcement_date)",
    "CREATE INDEX ix_violation_penalty_date ON violation (penalty_date)",
    "CREATE INDEX ix_violation_company_name ON violation (company_name)",
    "CREATE INDEX ix_violation_company_code ON violation (company_code)",
    "CREATE INDEX ix_environmentalviolation_violation_type ON environmentalviolation (violation_type)",
    "CREATE INDEX ix_environmentalviolation_tax_id ON environmentalviolation (tax_id)",
    "CREATE INDEX ix_environmentalviolation_company_name ON environmentalviolation (company_name)",
    "CREATE INDEX ix_environmentalviolation_disposition_no ON environmentalviolation (disposition_no)",
    "CREATE INDEX ix_environmentalviolation_violation_date ON environmentalviolation (violation_date)",
    "CREATE INDEX ix_environmentalviolation_company_code ON environmentalviolation (company_code)",
    "CREATE INDEX ix_environmentalviolation_penalty_date ON environmentalviolation (penalty_date)",
    "CREATE INDEX ix_non_manager_salary_market_type ON non_manager_salary (market_type)",
    "CREATE INDEX ix_non_manager_salary_company_name ON non_manager_salary (company_name)",
    "CREATE INDEX ix_non_manager_salary_year ON non_manager_salary (year)",
    "CREATE INDEX ix_non_manager_salary_raw_company_code ON non_manager_salary (raw_company_code)",
    "CREATE INDEX ix_non_manager_salary_company_code ON non_manager_salary (company_code)",
    "CREATE INDEX ix_employee_benefit_company_name ON employee_benefit (company_name)",
    "CREATE INDEX ix_employee_benefit_year ON employee_benefit (year)",
    "CREATE INDEX ix_employee_benefit_market_type ON employee_benefit (market_type)",
    "CREATE INDEX ix_employee_benefit_raw_company_code ON employee_benefit (raw_company_code)",
    "CREATE INDEX ix_employee_benefit_company_code ON employee_benefit (company_code)",
    "CREATE INDEX ix_welfare_policy_company_code ON welfare_policy (company_code)",
    "CREATE INDEX ix_welfare_policy_market_type ON welfare_policy (market_type)",
    "CREATE INDEX ix_welfare_policy_company_name ON welfare_policy (company_name)",
    "CREATE INDEX ix_welfare_policy_year ON welfare_policy (year)",
    "CREATE INDEX ix_welfare_policy_raw_company_code ON welfare_policy (raw_company_code)",
    "CREATE INDEX ix_salary_adjustment_raw_company_code ON salary_adjustment (raw_company_code)",
    "CREATE INDEX ix_salary_adjustment_market_type ON salary_adjustment (market_type)",
    "CREATE INDEX ix_salary_adjustment_year ON salary_adjustment (year)",
    "CREATE INDEX ix_salary_adjustment_company_name ON salary_adjustment (company_name)",
    "CREATE INDEX ix_salary_adjustment_company_code ON salary_adjustment (company_code)",
]

ALL_TABLES = [
    "salary_adjustment",
    "welfare_policy",
    "employee_benefit",
    "non_manager_salary",
    "environmentalviolation",
    "violation",
    "company",
]


def upgrade() -> None:
    for ddl in TABLES:
        op.execute(ddl)
    for ddl in INDEXES:
        op.execute(ddl)


def downgrade() -> None:
    for table in ALL_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table}")
