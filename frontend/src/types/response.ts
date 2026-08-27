/**
 * Transitional response type barrel.
 *
 * Canonical transport response definitions live under src/types/api/.
 * Remove this file after consumers import through the public api module.
 */

export type {
  ApiResponse,
  EmptyResponse,
  HealthResponse,
  ListResponse,
  MutationResponse,
  PaginatedResponse,
  PaginationMeta,
} from "./api/index";
