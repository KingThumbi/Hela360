# Migration 047 - Backend Current-Session Contract

## 1. Migration Purpose

Migration 047 establishes a backend-owned current-session contract that future
frontend authentication hydration can consume.

This migration adds one authenticated backend endpoint:

```text
GET /api/auth/session
```

It does not hydrate the frontend, implement frontend Authorization Context,
migrate query keys, change login response semantics, implement refresh/logout
routes, or modify frontend runtime source.

## 2. ADR Rules Applied

- ADR-004: response contracts are explicit schema dataclasses.
- ADR-005: authentication and authorization failures use existing backend
  exception/error semantics.
- ADR-006: tenant identity is derived server-side from the authenticated token
  and persisted session.
- ADR-007: effective permissions are computed by the backend authorization
  service.
- ADR-009: route and schema names use explicit session terminology.

## 3. Previous Blocker

Migration 046 selected:

```text
Path C - No verified identity source exists
```

The blocker was that frontend authentication could have valid tokens without a
verified identity/session endpoint capable of returning user, tenant, roles,
permissions, and branch context.

## 4. Existing Authentication Route

Blueprint:

```text
app.auth.bp
```

URL prefix:

```text
/api/auth
```

Confirmed existing login route:

```text
POST /api/auth/login
```

Login request schema:

```text
LoginRequest
```

Login response:

```text
LoginResponse
```

Login response remains token-only. This migration did not add identity fields
to login.

## 5. JWT Claim Findings

Access-token claims include:

- `sub`
- `user_id`
- `tenant_id`
- optional `branch_id`
- optional `role`
- optional `permissions`
- `session_id`
- `type`
- `jti`
- `iat`
- `nbf`
- `exp`
- `iss`
- `aud`

Refresh-token claims include:

- `sub`
- `user_id`
- `tenant_id`
- `session_id`
- `type`
- `jti`
- `iat`
- `nbf`
- `exp`
- `iss`
- `aud`

Refresh tokens intentionally omit branch, role, and permission claims.

## 6. Canonical Endpoint

Selected endpoint:

```text
GET /api/auth/session
```

Reason:

```text
The response represents the authenticated session and tenancy context, not only
a user profile.
```

No `/me` alias was registered.

## 7. Authentication Requirement

The route uses the existing JWT authentication decorator:

```python
@login_required
```

The service also rejects non-access-token identities.

## 8. Service Owner

New service owner:

```text
app/services/tenant/auth/current_session_service.py
```

Runtime singleton:

```text
current_session_service
```

The route delegates session assembly to this service and does not perform ORM
queries or permission aggregation directly.

## 9. Response Envelope

Response envelope:

```json
{
  "session": {
    "user": {},
    "tenant": {},
    "roles": [],
    "permissions": [],
    "branches": [],
    "default_branch_id": null
  }
}
```

No tokens, refresh-token identifiers, password hashes, security secrets, or
audit metadata are returned.

## 10. User Fields

Schema:

```text
CurrentSessionUserResponse
```

Fields:

- `id`
- `email`
- `username`
- `first_name`
- `last_name`
- `is_active`
- `is_locked`
- `is_owner`

`full_name` is not returned because the `User` model does not expose a verified
canonical full-name property.

## 11. Tenant Fields

Schema:

```text
CurrentSessionTenantResponse
```

Fields:

- `id`
- `name`
- `status`
- `is_active`

Tenant `name` maps to the verified backend `Tenant.display_name` field.

No tenant code is returned because no verified tenant code field exists on the
current `Tenant` model.

## 12. Role Fields

Schema:

```text
CurrentSessionRoleResponse
```

Fields:

- `id`
- `name`
- `code`

Roles are sorted deterministically by:

```text
code, name, id
```

## 13. Permission Fields

Permissions are returned as a sorted string list:

```json
"permissions": ["products.read", "sales.create"]
```

Effective permissions come from:

```text
AuthorizationService.refresh_context(...).permissions
```

The route does not duplicate permission aggregation logic.

## 14. Branch Fields

Schema:

```text
CurrentSessionBranchResponse
```

Fields:

- `id`
- `tenant_id`
- `name`
- `code`
- `is_active`

Branch behavior:

- if explicit branch assignments exist in `AuthorizationContext.branch_ids`,
  only those active branches are returned
- if branch assignments are empty, the current authorization contract grants
  tenant-wide branch access, so active tenant branches are returned
- inactive branches are not returned
- the JWT branch id must appear in the accessible branch list when present

## 15. Default Branch

Default branch disposition:

```text
default_branch_id: null
```

Reason:

```text
No persisted selected/default branch contract exists. User.branch_id and JWT
branch_id are not treated as frontend selected branch state.
```

## 16. Session Status Enforcement

The service enforces:

- access-token identity only
- active persisted session
- session user matches token user
- session tenant matches token tenant
- user resolution and status through `AuthorizationService.authorize`
- active tenant status
- authenticated branch must belong to accessible tenant branches when present

The implementation does not mutate session state.

## 17. Error Responses

Expected status behavior through existing handlers/decorators:

| Case | Expected status |
| --- | --- |
| Missing token | `401` |
| Invalid token | `401` |
| Refresh token used against session endpoint | `401` |
| Unknown user | `404` through existing handler |
| Inactive user | `403` through existing handler |
| Locked user | `423` through existing handler |
| Inactive tenant | `403` |
| Branch access failure | `403` |
| Authorization-context failure | Existing authorization error handling |

`flask routes` startup currently cannot verify global handlers because normal
startup is blocked by the pre-existing missing `argon2` dependency.

## 18. Route Registration

The route was verified with controlled blueprint registration:

```bash
venv/bin/python -c "... app.register_blueprint(routes.bp, url_prefix='/api/auth') ..."
```

Result:

```text
['/api/auth/session']
```

Normal route listing:

```bash
venv/bin/flask routes
```

Result:

```text
ModuleNotFoundError: No module named 'argon2'
```

No package was installed in this migration.

## 19. Tests Added

Added:

- `app/services/tenant/auth/tests/test_current_session_service.py`
- `app/services/tenant/auth/tests/test_current_session_route.py`

Coverage includes:

- missing token rejection
- registered route contract
- active authenticated response
- user id in response
- tenant id in response
- no password/token fields
- role ordering
- effective permission deduplication and sorting
- inactive session rejection
- inactive user rejection
- locked user rejection
- inactive tenant rejection
- branch scope validation
- no fabricated default branch
- tenant scope mismatch rejection

## 20. Test Results

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

## 21. Compile Results

Targeted compile:

```bash
venv/bin/python -m py_compile \
  app/auth/routes.py \
  app/auth/schemas.py \
  app/services/tenant/auth/current_session_service.py \
  app/services/tenant/auth/tests/test_current_session_service.py \
  app/services/tenant/auth/tests/test_current_session_route.py
```

Result:

```text
PASS
```

Broad compile:

```bash
venv/bin/python -m compileall app
```

Result:

```text
PASS
```

## 22. Pre-Existing Startup Blockers

Normal Flask startup remains blocked by:

```text
ModuleNotFoundError: No module named 'argon2'
```

Additional inspected pre-existing issue:

```text
app/services/tenant/auth/session_service.py imports AuthSession from
app.models.auth, but the registered model is UserSession in app.models.security.
```

This migration did not fix either unrelated startup concern.

## 23. Frontend DTO Implication

Future frontend DTO:

```text
CurrentSessionResponse
```

Expected mapping targets:

- `Identity`
- tenant query scope
- branch availability validation
- future Authorization Context
- transport tenant/branch storage synchronization

Frontend hydration is explicitly deferred.

## 24. Files Inspected

Inspected:

- `app/auth/routes.py`
- `app/auth/`
- `app/api/`
- `app/models/`
- `app/schemas/`
- `app/serializers/`
- `app/services/tenant/auth/`
- `app/services/tenant/administration/`
- `app/services/`
- `app/errors/`
- `app/api/errors.py`
- `app/api/utils.py`
- `app/services/tenant/auth/tests/`
- required frontend ADRs
- Migration 046 report

## 25. Files Created

- `app/services/tenant/auth/current_session_service.py`
- `app/services/tenant/auth/tests/test_current_session_service.py`
- `app/services/tenant/auth/tests/test_current_session_route.py`
- `frontend/docs/architecture/reviews/MIGRATION-047-BACKEND-CURRENT-SESSION-CONTRACT.md`

## 26. Files Modified

- `app/auth/routes.py`
- `app/auth/schemas.py`

Note:

```text
app/auth/routes.py already contained substantial dirty-worktree changes before
this migration. Migration 047 added the /session route and related imports
without reverting existing work.
```

## 27. Backend Behavior Confirmation

Confirmed:

- one current-session endpoint was added
- endpoint requires JWT authentication
- endpoint returns no token secrets
- route is read-only
- route performs no business side effects
- session assembly is service-owned
- effective permissions come from `AuthorizationService`
- login response semantics are unchanged

## 28. Frontend Source Confirmation

No frontend runtime source under `frontend/src` was modified by Migration 047.

Frontend verification:

```bash
cd frontend
npx tsc -b --pretty false
npm run build
```

Result:

```text
TypeScript exit code: 0
Vite build exit code: 0
```

Existing warning:

```text
Some chunks are larger than 500 kB after minification.
```

## 29. Invariants Verified

Verified:

1. one registered current-session endpoint exists
2. endpoint requires authentication
3. user identity comes from authenticated token/session
4. tenant identity is server-derived
5. client tenant headers do not drive ownership
6. effective permissions come from the authorization engine
7. roles and permissions are deterministic
8. branch data is not fabricated
9. selected branch is not conflated with accessible branches
10. no password or token secrets are exposed
11. route remains thin
12. shared logic is service-owned
13. existing error semantics are used
14. login behavior is unchanged
15. frontend runtime source remains unchanged
16. frontend TypeScript and Vite build remain successful

## 30. Rollback Boundary

Rollback for this migration is limited to:

- remove `GET /api/auth/session`
- remove current-session schema dataclasses
- remove `CurrentSessionService`
- remove the two focused current-session test files
- remove this migration report

No database migration, frontend runtime migration, or login-response migration
is involved.

## 31. Recommended Next Migration

Recommended next migration:

```text
Migration 048 - Frontend Current-Session DTO and Hydration Boundary
```

Goal:

```text
Add the frontend transport DTO and authService facade for GET /api/auth/session,
then hydrate Identity, tenant scope, and transport tenant/branch storage from
that single verified response.
```
