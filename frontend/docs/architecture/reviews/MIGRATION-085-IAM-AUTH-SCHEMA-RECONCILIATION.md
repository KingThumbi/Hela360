# Migration 085 - IAM/Auth Schema Reconciliation

## 1. Discovery During Migration 084

Migration 084 could not complete PostgreSQL runtime verification because the local PostgreSQL cluster was offline.

The live database was reported to have IAM/auth drift:

- missing `user_sessions`
- missing `refresh_tokens`
- missing `login_attempts`
- missing `password_reset_tokens`
- `user_roles` missing assignment metadata and timestamps
- `role_permissions` missing assignment metadata and timestamps
- `audit_logs` missing `session_id`, `status`, and `details`

## 2. Alembic Head vs Schema Equivalence

Alembic source head before Migration 085 was:

```text
f6a7b8c9d0e1
```

Migration 085 creates a new source head:

```text
a7b8c9d0e1f2
```

The live database could not be checked or upgraded because PostgreSQL remains unavailable from this session.

## 3. Missing Auth Tables

The migration creates:

- `user_sessions`
- `login_attempts`
- `refresh_tokens`
- `password_reset_tokens`

These are based on `app/models/security.py`.

## 4. Existing IAM Association-Table Shape

Existing association tables are retained:

- `user_roles`
- `role_permissions`

Their composite primary keys remain the uniqueness boundary.

## 5. Live Row Counts

Provided live counts before this migration:

```text
users: 1
roles: 1
permissions: 2
user_roles: 0
role_permissions: 0
audit_logs: 0
```

The counts were not re-read because PostgreSQL is offline.

## 6. Model Source of Truth

Inspected:

- `app/models/security.py`
- `app/models/auth.py`
- `app/models/audit.py`
- `migrations/versions/19b1ccd035ac_initial_schema.py`

## 7. New Tables

Revision `a7b8c9d0e1f2` explicitly creates the four missing auth/security tables.

No `db.create_all()` was used.

## 8. Session Fields

`user_sessions` includes:

- ownership: tenant, branch, user
- lifecycle: status, expiry, last activity
- device metadata
- authentication method/level/MFA timestamp
- revocation metadata
- timestamps

It includes `expires_at > created_at` and tenant/user cascade deletes.

## 9. Refresh-Token Fields

`refresh_tokens` includes:

- tenant/user/session ownership
- `jwt_id`
- token family
- expiry
- rotation metadata
- device metadata
- revocation metadata
- timestamps

It includes `jwt_id` uniqueness, `expires_at > created_at`, and cascade deletes through tenant/user/session.

## 10. Login-Attempt Fields

`login_attempts` records:

- nullable tenant
- email
- IP address
- user agent
- success flag
- failure reason
- timestamps

No User FK was added.

## 11. Password-Reset Fields

`password_reset_tokens` records:

- tenant/user ownership
- token hash
- expiry
- used/revoked timestamps
- request IP/user agent
- timestamps

It includes token hash uniqueness and `expires_at > created_at`.

## 12. user_roles Reconciliation

`user_roles` keeps composite PK `(user_id, role_id)`.

Added:

- `assigned_by_user_id`
- `assignment_reason`
- `created_at`
- `updated_at`
- `ix_user_roles_user`
- `ix_user_roles_role`

Foreign keys are replaced with `ON DELETE CASCADE` for user/role.

## 13. role_permissions Reconciliation

`role_permissions` keeps composite PK `(role_id, permission_id)`.

Added:

- `assigned_by_user_id`
- `assignment_reason`
- `created_at`
- `updated_at`

Foreign keys are replaced with `ON DELETE CASCADE` for role/permission.

## 14. audit_logs Reconciliation

Added:

- `session_id`
- `status`
- `details`
- `ix_audit_logs_session_id`
- `ix_audit_logs_status`

No session FK was invented.

## 15. Cascade-FK Decision

Cascade behavior was added only where current models require it:

- `user_sessions.tenant_id`
- `user_sessions.user_id`
- `login_attempts.tenant_id`
- `refresh_tokens.tenant_id`
- `refresh_tokens.user_id`
- `refresh_tokens.session_id`
- `password_reset_tokens.tenant_id`
- `password_reset_tokens.user_id`
- `user_roles.user_id`
- `user_roles.role_id`
- `role_permissions.role_id`
- `role_permissions.permission_id`

## 16. Timestamp Strategy

Existing empty association tables get timestamp columns with temporary `CURRENT_TIMESTAMP` server defaults, then the migration removes those server defaults.

This supports empty-table and possible legacy-row safety without introducing unintended database defaults.

## 17. Redundant Unique-Constraint Disposition

No duplicate physical unique constraints were added for:

- `uq_user_role`
- `uq_role_permission`

Composite PKs remain the real uniqueness boundary.

If future `flask db check` reports only those ORM metadata duplicates, the preferred fix is to simplify ORM metadata rather than add redundant constraints.

## 18. Enum Representation

Migration 085 uses `sa.Enum(..., native_enum=False)` for auth enums.

It does not introduce native PostgreSQL enum types.

## 19. Revision

Created:

```text
migrations/versions/a7b8c9d0e1f2_reconcile_iam_auth_schema.py
```

Revision:

```text
a7b8c9d0e1f2
```

Down revision:

```text
f6a7b8c9d0e1
```

## 20. Upgrade Result

Not run.

PostgreSQL is offline:

```text
pg_isready -h localhost -p 5432
localhost:5432 - no response
```

Attempting `sudo pg_ctlcluster 16 main start` required an interactive sudo password, so the cluster could not be started from this session.

## 21. Physical Schema Verification

Blocked because PostgreSQL is offline.

The following remain to be run once PostgreSQL is online:

```bash
psql -d hela360 -P pager=off -c "\d+ user_sessions"
psql -d hela360 -P pager=off -c "\d+ refresh_tokens"
psql -d hela360 -P pager=off -c "\d+ login_attempts"
psql -d hela360 -P pager=off -c "\d+ password_reset_tokens"
psql -d hela360 -P pager=off -c "\d+ user_roles"
psql -d hela360 -P pager=off -c "\d+ role_permissions"
psql -d hela360 -P pager=off -c "\d+ audit_logs"
```

## 22. ORM User Load Smoke

Blocked against real PostgreSQL because the database is offline.

## 23. Auth Runtime Smoke

Source auth suite passes:

```text
129 passed
```

Real PostgreSQL auth smoke is blocked until the migration is applied.

## 24. db Check Result

Blocked.

`flask db current` and `flask db check` require a live database connection.

## 25. Regression Totals

Migration file compile:

```text
venv/bin/python -m py_compile migrations/versions/a7b8c9d0e1f2_reconcile_iam_auth_schema.py
PASS
```

Backend compile:

```text
venv/bin/python -m compileall app
PASS
```

Auth suite:

```text
129 passed
```

Broader backend regression:

```text
205 passed, 4 warnings
```

Routes:

```text
FLASK_APP=app:create_app venv/bin/flask routes
PASS
```

## 26. Frontend Verification

TypeScript:

```text
npx tsc -b --pretty false
PASS
```

Production build:

```text
npm run build
PASS
```

Known Vite large-chunk warning remains.

## 27. Warnings

Known SQLAlchemy relationship overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

They were not changed in Migration 085.

## 28. Files Created

- `migrations/versions/a7b8c9d0e1f2_reconcile_iam_auth_schema.py`
- `frontend/docs/architecture/reviews/MIGRATION-085-IAM-AUTH-SCHEMA-RECONCILIATION.md`

## 29. Files Modified

No runtime source files were modified.

## 30. Remaining IAM Debt

Remaining work once PostgreSQL is online:

- run `flask db current`
- apply `flask db upgrade`
- verify new auth tables physically
- run `flask db check`
- run real PostgreSQL ORM User/session/refresh/reset smoke

Potential future metadata cleanup:

- remove redundant ORM unique constraints already covered by composite PKs if Alembic reports them as drift.
- address the four relationship overlap warnings separately.

## 31. Rollback Boundary

The downgrade for revision `a7b8c9d0e1f2`:

- drops dependent auth tables in dependency-safe order
- removes new audit fields/indexes
- removes association metadata/timestamps/indexes
- restores non-cascade association FKs
- does not drop `users`, `roles`, `permissions`, `audit_logs`, `user_roles`, or `role_permissions`

No live rollback was needed because the migration was not applied.

## 32. Return Point to Migration 084

After PostgreSQL is started and Migration 085 is applied, resume Migration 084 at the point where it needs the live runtime ProductUnit smoke:

```text
Goods Receipt:
2 boxes -> 200 base tablets -> KES 10/base cost

POS:
2 strips -> 20 base tablets deducted

Refund:
1 strip -> 10 base tablets restored
```

Do not begin pack/unit frontend UI yet.
