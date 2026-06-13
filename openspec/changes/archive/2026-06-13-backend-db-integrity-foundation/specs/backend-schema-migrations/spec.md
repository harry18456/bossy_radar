## ADDED Requirements

### Requirement: Schema SHALL be managed by versioned migrations

The backend SHALL manage both the main and archive SQLite schemas through Alembic migrations rather than runtime create_all calls. A single migrations package SHALL apply the same migration scripts to both the main engine and the archive engine, each tracking its own version. Service code SHALL NOT call SQLModel.metadata.create_all to establish production schema.

#### Scenario: Upgrade a clean database

- **WHEN** alembic upgrade head runs against an empty SQLite database
- **THEN** the resulting schema SHALL contain every model table with its unique constraints

#### Scenario: Both engines are migrated

- **WHEN** the migration command runs without restricting the target
- **THEN** both the main and the archive database SHALL be upgraded to the same head revision
- **THEN** each database SHALL record the applied revision in its own alembic_version table

#### Scenario: Downgrade is reversible

- **WHEN** alembic downgrade is run from head to the baseline revision
- **THEN** the post-baseline schema changes SHALL be reverted without error

### Requirement: Existing databases SHALL migrate in place without data loss

Migrating an existing populated database SHALL preserve every row. The baseline revision SHALL be stampable on an already-populated database so that only post-baseline migrations execute against it.

#### Scenario: In-place migration preserves rows

- **WHEN** an existing database is stamped at the baseline revision and then upgraded to head
- **THEN** each table's row count after the upgrade SHALL equal its row count before the upgrade
