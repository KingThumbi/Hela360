/**
 * ============================================================================
 * Hela360 Shared Type System
 * ============================================================================
 *
 * Public export surface for all shared application types.
 *
 * Architecture
 * ------------
 *
 * • Entities
 * • Request DTOs
 * • Response DTOs
 * • Enumerations
 *
 * ============================================================================
 */

export * from "./entities";
export * from "./requests";
export * from "./responses";
export * from "./enums";
export type {
  ApiError,
  ApiResponse,
  EmptyResponse,
  EntityId,
  HealthResponse,
  HttpMethod,
  ListResponse,
  MutationResponse,
  PaginatedResponse,
  PaginationMeta,
  RequestConfig,
  ValidationError,
} from "./api/index";
export {
  ERROR_CODES,
} from "./enums/error-code";
export type {
  ErrorCode,
} from "./enums/error-code";
export type {
  NavigationItem,
  NavigationItemId,
  NavigationSection,
  NavigationSectionId,
} from "./navigation";
export type {
  BranchQueryScope,
  QueryScope,
  QueryScopeReadiness,
  TenantQueryScope,
} from "./domains/query-scope";
