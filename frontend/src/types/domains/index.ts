/**
 * ============================================================================
 * Hela360 Domain Type Registry
 * ============================================================================
 *
 * Public export surface for all business domains.
 *
 * ============================================================================
 */

export * from "./sales";
export * from "./inventory";
export * from "./procurement";
export * from "./finance";
export * from "./customers";
export type {
  BranchQueryScope,
  QueryScope,
  QueryScopeReadiness,
  TenantQueryScope,
} from "./query-scope";
