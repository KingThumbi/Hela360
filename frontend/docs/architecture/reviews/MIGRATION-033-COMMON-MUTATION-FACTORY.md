# Migration 033 - Common Mutation Factory Arity Alignment

## 1. Migration Purpose

Migration 033 aligns the shared CRUD mutation hooks with the installed
TanStack Query v5 mutation callback contract.

The common create, update, and delete mutation hooks composed caller
`onSuccess` callbacks with the older three-argument callback shape. TanStack
Query v5.101.2 expects four callback arguments:

```text
data, variables, onMutateResult, context
```

## 2. ADR Rules Applied

- ADR-001: services remain free of React Query and cache invalidation behavior.
- ADR-002: mutation hooks invoke services and expose mutation state.
- ADR-003: cache invalidation remains centralized in `queryInvalidation.ts`.
- ADR-004: business DTO/entity types remain in `src/types`.
- ADR-005: mutation errors continue to use the existing TanStack `DefaultError`
  contract in the current common hooks.
- ADR-008: shared hook infrastructure remains in the common query-hook
  boundary.
- ADR-009: generic names now use the installed library's semantic
  `TOnMutateResult` name.

## 3. Installed TanStack Query Version

Installed version:

```text
@tanstack/react-query 5.101.2
```

Verified v5 generic ordering:

```typescript
UseMutationOptions<TData, TError, TVariables, TOnMutateResult>
UseMutationResult<TData, TError, TVariables, TOnMutateResult>
MutationFunction<TData, TVariables>
```

Verified v5 `onSuccess` shape:

```typescript
onSuccess(
  data,
  variables,
  onMutateResult,
  context,
)
```

## 4. Exact Initial Diagnostics

Before migration:

```text
src/hooks/queries/common/useCreateEntity.ts(104,26): error TS2554: Expected 4 arguments, but got 3.
src/hooks/queries/common/useDeleteEntity.ts(104,26): error TS2554: Expected 4 arguments, but got 3.
src/hooks/queries/common/useUpdateEntity.ts(33,8): error TS6133: 'QueryClient' is declared but its value is never read.
src/hooks/queries/common/useUpdateEntity.ts(114,26): error TS2554: Expected 4 arguments, but got 3.
```

All four diagnostics shared one root migration issue: common CRUD mutation
hooks were still forwarding the older three-argument `onSuccess` callback
shape while using TanStack Query v5 types.

## 5. Mutation Factories Found

Canonical options factory:

```text
frontend/src/lib/queryFactory.ts::createMutationOptions
```

Common mutation hooks:

- `frontend/src/hooks/queries/common/useCreateEntity.ts`
- `frontend/src/hooks/queries/common/useUpdateEntity.ts`
- `frontend/src/hooks/queries/common/useDeleteEntity.ts`

Direct `useMutation` hooks also exist in auth, inventory, procurement, and
sales domains. Those were inspected but not rewritten because their diagnostics
are unrelated domain contract drift.

No `mutationFactory.ts`, `createMutationHook`, `useAppMutation`, or
`useEntityMutation` implementation was found.

## 6. Canonical Mutation Factory Owner

Canonical options builder:

```text
frontend/src/lib/queryFactory.ts::createMutationOptions
```

Canonical common CRUD mutation behavior:

```text
frontend/src/hooks/queries/common/
```

## 7. Pre-Migration Signature

`createMutationOptions` already used the correct positional factory shape:

```typescript
createMutationOptions<TData, TVariables, TContext>(
  mutationFn,
  options?,
)
```

The common CRUD hooks exposed a fourth generic named `TContext`, but in
TanStack Query v5 that generic semantically represents `TOnMutateResult`.

## 8. Canonical Signature

`createMutationOptions` remains positional and unchanged:

```typescript
createMutationOptions<TData, TVariables, TOnMutateResult>(
  mutationFn,
  options?,
)
```

Common CRUD hooks now use:

```typescript
useCreateEntity<TResult, TCreate, TOnMutateResult = unknown>(...)
useUpdateEntity<TResult, TUpdate, TOnMutateResult = unknown>(...)
useDeleteEntity<TResult = void, TOnMutateResult = unknown>(...)
```

## 9. Generic Parameter Contract

- `TResult`: service-returned mutation result
- `TCreate`: create request payload
- `TUpdate`: update request payload
- `EntityId`: delete mutation variable
- `TOnMutateResult`: result returned by caller `onMutate`

No broad `any` was introduced.

## 10. Argument and Arity Disposition

The public hook arity remains unchanged:

```text
mutationFn, invalidate?, options?
```

The internal callback forwarding now passes all four TanStack Query v5
arguments to caller `options.onSuccess`.

## 11. Callback Ownership

Existing ordering was preserved:

1. mutation function executes through TanStack Query
2. common hook `onSuccess` runs
3. centralized invalidation callback runs, if supplied
4. caller `options.onSuccess` runs

Only the forwarded callback arity changed.

## 12. Invalidation Integration

Invalidation remains selected by domain hooks and executed through centralized
helpers from:

```text
frontend/src/lib/queryInvalidation.ts
```

No query key or invalidation policy changed.

## 13. Hook Legality Verification

`useCreateEntity`, `useUpdateEntity`, and `useDeleteEntity` are React hooks.

They call:

- `useQueryClient`
- `useMutation`

at hook top level and are intended to be called by domain hooks/components.

No hook is called at module scope or inside a callback.

`createMutationOptions` does not call hooks.

## 14. Common Option-Type Disposition

The caller-safe options remain:

```typescript
Omit<
  UseMutationOptions<...>,
  "mutationFn"
>
```

Callers still cannot override the hook-owned `mutationFn`.

No new shared mutation option alias was introduced because the existing inline
contracts are narrow and only needed v5 arity alignment.

## 15. Consumers Inspected

Inspected factory/common consumers:

- `useCreateEntity`
- `useUpdateEntity`
- `useDeleteEntity`
- `useLogin`
- `useLogout`
- `useDeleteCustomer`
- `useDeleteProduct`
- direct mutation hooks in inventory, procurement, and sales

## 16. Consumers Changed

Changed:

- `frontend/src/hooks/queries/common/useCreateEntity.ts`
- `frontend/src/hooks/queries/common/useUpdateEntity.ts`
- `frontend/src/hooks/queries/common/useDeleteEntity.ts`

No domain hook call sites were changed.

## 17. Unsupported Consumers Retained

Unsupported or drifting domain operations were not fixed, including:

- customer update response shape drift
- dashboard hook/service method-name drift
- inventory missing entity/request/service operations
- procurement placeholder entity/request/service operations
- sales service reconstruction issues

## 18. Files Inspected

- `frontend/src/lib/queryFactory.ts`
- `frontend/src/lib/queryInvalidation.ts`
- `frontend/src/hooks/queries/common/`
- `frontend/src/hooks/queries/auth/`
- `frontend/src/hooks/queries/products/`
- `frontend/src/hooks/queries/customers/`
- `frontend/src/hooks/queries/inventory/`
- `frontend/src/hooks/queries/procurement/`
- `frontend/src/hooks/queries/sales/`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/node_modules/@tanstack/react-query/`
- `frontend/node_modules/@tanstack/query-core/`
- ADR-001
- ADR-002
- ADR-003
- ADR-004
- ADR-005
- ADR-008
- ADR-009
- Migration 012

## 19. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-033-COMMON-MUTATION-FACTORY.md`

## 20. Files Modified

- `frontend/src/hooks/queries/common/useCreateEntity.ts`
- `frontend/src/hooks/queries/common/useUpdateEntity.ts`
- `frontend/src/hooks/queries/common/useDeleteEntity.ts`

## 21. Compiler Errors Before

Pre-migration baseline:

```text
104 TypeScript errors
```

## 22. Compiler Errors After

Post-migration result:

```text
100 TypeScript errors
```

## 23. Net Reduction

```text
104 -> 100
```

Net reduction:

```text
4 TypeScript errors
```

## 24. Mutation-Factory Diagnostics Before and After

Before:

- three `Expected 4 arguments, but got 3` diagnostics in common mutation
  callback forwarding
- one unused `QueryClient` import diagnostic in `useUpdateEntity`

After:

- no `useCreateEntity` mutation arity diagnostic
- no `useUpdateEntity` mutation arity diagnostic
- no `useDeleteEntity` mutation arity diagnostic
- no `useUpdateEntity` unused `QueryClient` diagnostic

## 25. Newly Exposed Diagnostics

The next exposed top diagnostic is unrelated to the common mutation factory:

```text
src/hooks/queries/customers/useUpdateCustomer.ts(57,7): Type 'Promise<ApiResponse<Customer>>' is not assignable to type 'Promise<Customer>'.
```

## 26. New Diagnostics

No new diagnostics were introduced.

## 27. Remaining Mutation Blockers

Remaining mutation-related blockers are domain contract issues rather than
common factory arity issues:

- customer update service returns `ApiResponse<Customer>` where hook expects
  `Customer`
- inventory workflow hooks reference missing types/service methods
- procurement mutation hooks reference missing types/service methods
- sales mutation hooks reference missing request types/service methods

## 28. Runtime Behavior Confirmation

Runtime behavior is preserved.

The mutation function, invalidation callback, caller callback order, query
client usage, and public hook call signatures remain unchanged.

The only runtime-relevant difference is that caller `onSuccess` callbacks now
receive the full TanStack Query v5 argument list.

## 29. Invariants Verified

- Shared mutation behavior has one canonical common owner.
- The callback contract matches installed TanStack Query v5.101.2 types.
- Generic parameters are used and ordered consistently.
- Mutation functions continue to return domain results.
- Hooks do not unwrap transport envelopes in this migration.
- Services contain no mutation/cache logic.
- Invalidation policy remains centralized.
- Caller callback order remains behaviorally equivalent.
- Rules of Hooks are respected.
- Unsupported operations remain unsupported.
- No query key changed.
- No backend file was changed.
- No unrelated domain behavior changed.

## 30. Rollback Boundary

Rollback is limited to:

- `frontend/src/hooks/queries/common/useCreateEntity.ts`
- `frontend/src/hooks/queries/common/useUpdateEntity.ts`
- `frontend/src/hooks/queries/common/useDeleteEntity.ts`
- this review document

No service, DTO, query key, invalidation policy, provider, store, route,
navigation, backend, or feature UI rollback is required.

## 31. Recommended Next Migration

Recommended next migration:

```text
Customer Update Mutation Response Alignment
```

The next top compiler diagnostic is:

```text
src/hooks/queries/customers/useUpdateCustomer.ts(57,7): Type 'Promise<ApiResponse<Customer>>' is not assignable to type 'Promise<Customer>'.
```
