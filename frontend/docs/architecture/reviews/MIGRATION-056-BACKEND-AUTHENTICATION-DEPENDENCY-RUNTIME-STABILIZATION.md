# Migration 056 - Backend Authentication Dependency And Runtime Stabilization

## 1. Migration Purpose

Migration 056 stabilizes normal backend application startup through the Flask
application factory by making the authentication dependency contract
reproducible and correcting narrow auth-bootstrap import/registration blockers.

No Product, Customer, Inventory, Procurement, Sales, Finance, or frontend
feature work was performed.

## 2. Dependency Ownership

Only one Python dependency manifest exists:

```text
requirements.txt
```

No `requirements-dev.txt`, `pyproject.toml`, `poetry.lock`, `Pipfile`,
`setup.py`, `setup.cfg`, `render.yaml`, `Procfile`, `Dockerfile`, or
`runtime.txt` was found.

Therefore `requirements.txt` is the canonical production/development
dependency manifest currently present in the repository.

## 3. Password Service Contract

Inspected:

```text
app/services/tenant/auth/password_service.py
app/services/tenant/auth/authentication_service.py
app/auth/
```

The password service imports:

```python
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError
```

Import package:

```text
argon2
```

Python distribution:

```text
argon2-cffi
```

## 4. Hashing Behavior

Existing behavior was preserved:

- new hashes use Argon2 through `PasswordHasher`;
- hashes starting with `$argon2` are verified with Argon2;
- non-Argon2 hashes fall back to Werkzeug `check_password_hash`;
- `needs_rehash` returns true for missing, legacy, invalid, or outdated hashes;
- `upgrade_hash_if_needed` only creates an upgraded hash after successful
  password verification.

No password algorithm, parameters, fallback behavior, or security model was
changed.

## 5. Dependency Decision

Path B was selected:

```text
code depends on Argon2 but dependency is undeclared
```

Added to `requirements.txt` using the existing exact-pin style:

```text
argon2-cffi==23.1.0
```

The dependency is declared once.

## 6. Installation Verification

Initial sandboxed install failed because package-index access was unavailable.

After approval, the canonical install command succeeded:

```bash
venv/bin/pip install -r requirements.txt
```

Installed distribution:

```text
argon2-cffi 23.1.0
```

## 7. Import Verification

Commands:

```bash
venv/bin/python -c "from argon2 import PasswordHasher; print('argon2 ok')"
venv/bin/python -c "from app.services.tenant.auth.password_service import PasswordService; print('password service ok')"
```

Result:

```text
PASS
```

## 8. Secondary Bootstrap Fixes

Once Argon2 was available, two narrow startup blockers surfaced.

### Password Service Module API

`authentication_service.py` imports module-level helpers:

- `hash_password`
- `verify_password`
- `upgrade_hash_if_needed`
- `validate_password`

`password_service.py` had only singleton methods. Thin module-level wrappers
were added around the existing `password_service` singleton.

This preserves the existing hashing implementation and restores the expected
auth service import boundary.

### Session Model Import

`session_service.py` imported:

```python
from app.models.auth import AuthSession
```

The canonical model is:

```text
app.models.security.UserSession
```

The service now imports and annotates `UserSession` directly.

### Auth Blueprint Registration

`register_blueprints()` registered the auth blueprint before auth routes were
imported, then called `init_auth(app)`, which imported routes and registered the
same blueprint again.

The application factory now lets `init_auth(app)` own auth route import and
auth blueprint registration exactly once.

## 9. Application Factory Verification

Command:

```bash
venv/bin/python - <<'PY'
from app import create_app
app = create_app()
print(app.name)
print("app factory ok")
PY
```

Result:

```text
app
app factory ok
```

## 10. Route Listing Verification

Command:

```bash
FLASK_APP=app:create_app venv/bin/flask routes
```

Result:

```text
PASS
```

Verified visible routes include:

- `/api/auth/login`
- `/api/auth/session`
- `/api/products`
- `/api/customers`
- `/api/suppliers`
- `/api/sales/checkout`
- `/api/sales/<sale_id>/refund`
- `/api/health`

## 11. Health Endpoint Verification

Flask test-client smoke result:

```text
GET /api/health -> 200
```

Response:

```json
{
  "ok": true,
  "service": "hela360",
  "status": "healthy"
}
```

## 12. Password Smoke Test

Safe password-service smoke test verified:

- generated hash starts with `$argon2`;
- correct password verifies true;
- incorrect password verifies false.

No plaintext password, token, or hash was logged in application code.

## 13. Current-Session Regression

Command:

```bash
venv/bin/python -m pytest \
  app/services/tenant/auth/tests/test_current_session_service.py \
  app/services/tenant/auth/tests/test_current_session_route.py \
  -q
```

Result:

```text
13 passed
```

## 14. Product Regression

Command:

```bash
venv/bin/python -m pytest app/api/tests/test_products_list_contract.py -q
```

Result:

```text
8 passed
```

Existing warning:

```text
4 SQLAlchemy relationship overlap warnings
```

## 15. Supplier Regression

Command:

```bash
venv/bin/python -m pytest app/services/tenant/procurement/tests/test_supplier_contract.py -q
```

Result:

```text
6 passed
```

Existing warning:

```text
4 SQLAlchemy relationship overlap warnings
```

## 16. Broader Auth Tests

Command:

```bash
venv/bin/python -m pytest app/services/tenant/auth/tests -q
```

Result:

```text
129 passed
```

## 17. Backend Compile And Dependency Checks

Commands:

```bash
venv/bin/python -m py_compile \
  app/services/tenant/auth/password_service.py \
  app/services/tenant/auth/session_service.py \
  app/__init__.py

venv/bin/python -m compileall app
venv/bin/pip check
```

Results:

```text
py_compile: PASS
compileall app: PASS
pip check: No broken requirements found.
```

`pip check` also printed a cache-directory ownership warning, but dependency
resolution itself passed.

## 18. Database Startup Verification

Command:

```bash
FLASK_APP=app:create_app venv/bin/flask db current
```

Result:

```text
BLOCKED after app startup by psycopg2/SQLAlchemy OperationalError
```

This indicates the Flask app now boots far enough to invoke Flask-Migrate, but
the configured PostgreSQL database is not reachable in the current environment.

No database migrations were run.

## 19. Frontend Verification

No frontend source changes were required.

Commands:

```bash
cd frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript errors: 0
Vite build: PASS
```

Existing Vite warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

## 20. Files Inspected

- `requirements.txt`
- `app/services/tenant/auth/password_service.py`
- `app/services/tenant/auth/authentication_service.py`
- `app/services/tenant/auth/session_service.py`
- `app/auth/__init__.py`
- `app/auth/routes.py`
- `app/auth/`
- `app/models/auth.py`
- `app/models/security.py`
- `app/models/__init__.py`
- `app/__init__.py`
- `run.py`
- existing auth, Product, and Supplier targeted tests

## 21. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-056-BACKEND-AUTHENTICATION-DEPENDENCY-RUNTIME-STABILIZATION.md`

## 22. Files Modified

- `requirements.txt`
- `app/services/tenant/auth/password_service.py`
- `app/services/tenant/auth/session_service.py`
- `app/__init__.py`

## 23. Security Constraints Preserved

This migration did not:

- downgrade password hashing;
- log plaintext passwords;
- log tokens;
- weaken Argon2 parameters;
- bypass verification;
- introduce default credentials;
- expose password hashes through APIs.

## 24. Invariants Verified

- `argon2-cffi` is declared reproducibly.
- `argon2.PasswordHasher` imports successfully.
- password service imports successfully.
- authentication service imports successfully.
- `create_app()` succeeds.
- `flask routes` succeeds.
- `/api/health` responds successfully.
- auth/session routes are registered.
- Product, Customer, Supplier, and Sales routes are registered.
- Current-session tests pass.
- Product list tests pass.
- Supplier contract tests pass.
- Auth test suite passes.
- `pip check` passes.
- Frontend TypeScript remains clean.
- Frontend production build remains successful.

## 25. Remaining Runtime Limitation

Database migration-state inspection is blocked by local PostgreSQL
connectivity/configuration:

```text
sqlalchemy.exc.OperationalError
```

This is no longer an authentication dependency/bootstrap failure.

## 26. Rollback Boundary

Rollback is limited to:

- removing `argon2-cffi==23.1.0` from `requirements.txt`;
- removing module-level password-service wrappers;
- restoring the stale `AuthSession` session-service import;
- restoring duplicate auth blueprint registration behavior;
- removing this migration report.

## 27. Recommended Next Migration

Recommended next migration:

```text
Migration 057 - Backend Database Connectivity And Migration-State Verification
```
