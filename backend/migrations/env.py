"""Alembic environment driving BOTH the main and archive SQLite engines.

When sqlalchemy.url is set (tests), a single database is targeted. Otherwise
production migrations are applied to the main engine and the archive engine in
turn, each tracking its own alembic_version. Foreign keys are disabled for the
duration of a migration so SQLite batch table rebuilds can move data without
tripping the company_code references.
"""

import contextlib
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlmodel import SQLModel

# Import every model so all tables are registered on SQLModel.metadata.
from app.db.session import archive_engine, engine
from app.models.company import Company  # noqa: F401
from app.models.employee_benefit import EmployeeBenefit  # noqa: F401
from app.models.environmental_violation import EnvironmentalViolation  # noqa: F401
from app.models.non_manager_salary import NonManagerSalary  # noqa: F401
from app.models.salary_adjustment import SalaryAdjustment  # noqa: F401
from app.models.violation import Violation  # noqa: F401
from app.models.welfare_policy import WelfarePolicy  # noqa: F401

config = context.config

if config.config_file_name is not None:
    # disable_existing_loggers=False so loading this env (e.g. from the test
    # suite) does not silence the application's loggers.
    with contextlib.suppress(Exception):
        fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = SQLModel.metadata


def _target_engines():
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return [create_engine(url)]
    return [engine, archive_engine]


def run_migrations_offline() -> None:
    for eng in _target_engines():
        context.configure(
            url=str(eng.url),
            target_metadata=target_metadata,
            literal_binds=True,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    # The data tables only REFERENCE company; nothing references them, so the
    # batch copy-and-move rebuilds run fine with foreign_keys enforced. Running
    # in the default transactional mode means a failed migration rolls back
    # cleanly instead of leaving a half-migrated database.
    for eng in _target_engines():
        with eng.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
