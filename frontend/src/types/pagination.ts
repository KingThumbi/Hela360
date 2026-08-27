/**
 * Transitional pagination type barrel.
 *
 * Canonical response pagination lives under src/types/api/.
 * Canonical request pagination lives under src/types/requests/.
 */

export type {
  PaginatedResponse,
  PaginationMeta,
} from "./api/index";

export type {
  PaginationRequest,
} from "./requests/index";
