/**
 * Canonical TanStack Query cache scope contracts.
 *
 * These types describe cache identity only. They do not imply transport
 * headers, backend tenancy enforcement, authorization, or UI switching.
 */

export interface TenantQueryScope {
  readonly tenantId: string;
}

export interface BranchQueryScope extends TenantQueryScope {
  readonly branchId: string;
}

export type QueryScope = TenantQueryScope | BranchQueryScope;

export interface QueryScopeReadiness {
  readonly tenantId: string | null;
  readonly branchId: string | null;
  readonly tenantScope: TenantQueryScope | null;
  readonly branchScope: BranchQueryScope | null;
  readonly isTenantScopeReady: boolean;
  readonly isBranchScopeReady: boolean;
}
