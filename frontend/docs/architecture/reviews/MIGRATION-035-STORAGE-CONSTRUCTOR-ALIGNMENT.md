# Migration 035 - Storage Constructor Alignment

## 1. Migration Purpose

Migration 035 aligns the canonical frontend storage module with the active
TypeScript compiler setting:

```json
"erasableSyntaxOnly": true
```

The migration replaces constructor parameter-property syntax with equivalent
erasable TypeScript syntax. Runtime storage behavior, persistence keys,
serialization, authentication semantics, and public APIs are unchanged.

## 2. Exact Initial Diagnostic

Frontend compiler baseline before this migration:

```text
99 TypeScript errors
```

Storage diagnostic before:

```text
src/lib/storage.ts(89,5): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
```

Diagnostic details:

- diagnostic code: `TS1294`
- exact line: `frontend/src/lib/storage.ts:89`
- rejected syntax: constructor parameter property
- affected class: `StorageService`
- parameter properties found in `storage.ts`: one
- other storage diagnostics before: none
- enums, namespaces, decorators, import-equals syntax, or other prohibited
  non-erasable syntax in `storage.ts`: none found

## 3. Compiler Settings Applied

Authoritative settings inspected in:

```text
frontend/tsconfig.app.json
```

Relevant settings:

```json
"verbatimModuleSyntax": true,
"erasableSyntaxOnly": true
```

No compiler settings were changed.

## 4. Storage Module Owner

Canonical storage owner:

```text
frontend/src/lib/storage.ts
```

The module owns:

- `StorageAdapter`
- `LocalStorageAdapter`
- `StorageService`
- `storage`
- the default storage export

No competing active storage implementation was found.

## 5. Constructor Before

Before:

```typescript
export class StorageService {
  constructor(
    private readonly adapter: StorageAdapter,
  ) {}
}
```

This syntax requires TypeScript runtime emit and is rejected by
`erasableSyntaxOnly`.

## 6. Constructor After

After:

```typescript
export class StorageService {
  private readonly adapter: StorageAdapter;

  constructor(adapter: StorageAdapter) {
    this.adapter = adapter;
  }
}
```

The field remains:

- `private`
- `readonly`
- typed as `StorageAdapter`
- initialized during construction

Constructor call sites remain unchanged.

## 7. Public API Confirmation

No public storage API changed.

Preserved public symbols:

- `StorageAdapter`
- `LocalStorageAdapter`
- `StorageService`
- `storage`
- default export `storage`

Preserved method contracts include:

- `get<T>(key): T | null`
- `set<T>(key, value): void`
- `remove(key): void`
- `clear(): void`
- token helpers
- theme helpers
- sidebar helpers
- tenant helpers
- branch helpers
- remember-me helpers
- `clearSession()`

## 8. Persistence-Key Confirmation

Persistence keys remain owned by:

```text
frontend/src/constants/storage.ts
```

Keys were inspected and not changed:

- `hela360.access_token`
- `hela360.refresh_token`
- `hela360.theme`
- `hela360.sidebar.collapsed`
- `hela360.tenant.id`
- `hela360.branch.id`
- `hela360.remember_me`

## 9. Serialization Confirmation

Storage serialization behavior is unchanged:

- missing keys still return `null`
- raw string values are stored as raw strings
- non-string values still use `JSON.stringify`
- reads still use `JSON.parse`
- malformed JSON still falls back to the stored string value
- adapter exceptions are not newly swallowed
- no new default values were introduced

## 10. Authentication Behavior Confirmation

Authentication consumers were inspected:

- `frontend/src/store/authStore.ts`
- `frontend/src/api/interceptors.ts`
- `frontend/src/api/refresh.ts`
- `frontend/src/providers/AuthProvider.tsx`
- `frontend/src/hooks/queries/auth/useLogout.ts`

This migration does not change:

- token persistence
- token lookup
- logout cleanup
- refresh sequencing
- authentication initialization
- identity persistence
- tenant state
- branch state

## 11. Files Inspected

- `frontend/src/lib/storage.ts`
- `frontend/src/constants/storage.ts`
- `frontend/src/store/authStore.ts`
- `frontend/src/store/shellStore.ts`
- `frontend/src/api/interceptors.ts`
- `frontend/src/api/refresh.ts`
- `frontend/src/api/`
- `frontend/src/providers/`
- `frontend/tsconfig.app.json`
- `frontend/package.json`
- ADR-005
- ADR-008
- ADR-009
- Migration 002 report
- Migration 005 report
- Migration 006 report

## 12. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-035-STORAGE-CONSTRUCTOR-ALIGNMENT.md`

## 13. Files Modified

- `frontend/src/lib/storage.ts`

No auth store, shell store, provider, API, service, query, route, navigation, or
backend source file was modified.

## 14. Compiler Errors Before

```text
99 TypeScript errors
```

## 15. Compiler Errors After

```text
98 TypeScript errors
```

Net reduction:

```text
1 error
```

## 16. Storage Diagnostics Before and After

Before:

```text
src/lib/storage.ts(89,5): error TS1294
```

After:

```text
none
```

Parameter-property diagnostics after:

```text
none
```

Import diagnostics after:

```text
none in storage.ts
```

## 17. Build Verification

Commands run:

```bash
npx tsc -b --pretty false
npm run build
```

`npx tsc -b --pretty false` reports 98 remaining TypeScript errors, down from
99.

`npm run build` exits with code 2 because it runs `tsc -b` before Vite and the
repository still has the unrelated 98-error backlog.

No `storage.ts` diagnostic remains in either verification output.

## 18. New Diagnostics

No new diagnostics were introduced by this migration.

Remaining global diagnostic categories are unchanged and include dashboard,
inventory, procurement, sales, theme import, query factory, main entry, and
service barrel contract drift.

## 19. Remaining Storage Blockers

No remaining storage compiler blocker was found.

This migration does not audit browser availability guards beyond preserving the
existing direct `window.localStorage` adapter behavior.

## 20. Runtime Behavior Confirmation

Expected runtime diff:

```text
zero
```

The same adapter instance is passed to `StorageService`, assigned during
construction, and used by the same methods. Only TypeScript-only constructor
syntax changed.

## 21. Invariants Verified

- Storage has one canonical module owner.
- The adapter dependency remains explicit.
- Constructor behavior remains equivalent.
- Public storage APIs remain unchanged.
- Persistence keys remain unchanged.
- Serialization remains unchanged.
- Authentication token behavior remains unchanged.
- TypeScript syntax is compatible with `erasableSyntaxOnly`.
- `verbatimModuleSyntax` remains satisfied.
- No backend file changed.
- No unrelated frontend behavior changed.

## 22. Rollback Boundary

Rollback is limited to:

- `frontend/src/lib/storage.ts`
- this review document

## 23. Recommended Next Migration

Recommended next migration:

```text
Migration 036 - Theme Type-Only Import Alignment
```

Rationale:

The remaining isolated syntax/import diagnostic is:

```text
src/hooks/useTheme.ts(4,3): error TS1484
```

It appears to be another narrow compiler-configuration alignment under
`verbatimModuleSyntax`.

