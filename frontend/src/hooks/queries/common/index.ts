/**
 * ============================================================================
 * Hela360 Enterprise Common Query Hooks
 * ============================================================================
 *
 * Reusable TanStack Query hooks shared across all feature modules.
 *
 * These hooks provide the foundation for CRUD operations throughout Hela360.
 *
 * ============================================================================
 */

export {
  useEntity,
} from "./useEntity";
export type {
  UseEntityOptions,
} from "./useEntity";

export {
  useEntityList,
} from "./useEntityList";

export {
  usePaginatedQuery,
} from "./usePaginatedQuery";

export {
  useCreateEntity,
  type InvalidateCallback,
} from "./useCreateEntity";

export {
  useUpdateEntity,
  type UpdateEntityPayload,
} from "./useUpdateEntity";

export {
  useDeleteEntity,
  type EntityId,
} from "./useDeleteEntity";

export {
  useSearchQuery,
} from "./useSearchQuery";
