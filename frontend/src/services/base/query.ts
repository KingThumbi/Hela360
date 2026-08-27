/**
 * ============================================================================
 * Hela360 Frontend
 * Query & Pagination Types
 * ============================================================================
 *
 * Shared query abstractions used by all BaseService-derived services.
 */

import type { EntityIdentifier } from "./types";

/**
 * Primitive values accepted as query parameters.
 */
export type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined;

/**
 * Filter values.
 */
export type FilterValue =
  | QueryValue
  | readonly QueryValue[];

/**
 * Generic filter object.
 */
export type FilterOptions<TEntity> =
  Partial<Record<keyof TEntity, FilterValue>>;

/**
 * Pagination.
 */
export interface PaginationOptions {
  page?: number;
  pageSize?: number;
}

/**
 * Search.
 */
export interface SearchOptions {
  search?: string;
}

/**
 * Sort direction.
 */
export type SortDirection =
  | "asc"
  | "desc";

/**
 * Entity sort key.
 */
export type SortKey<TEntity> =
  Extract<keyof TEntity, string>;

/**
 * Sorting options.
 */
export interface SortOptions<TEntity> {
  sortBy?: SortKey<TEntity>;
  sortDirection?: SortDirection;
}

/**
 * Generic query object.
 */
export interface QueryOptions<TEntity>
  extends PaginationOptions,
    SearchOptions,
    SortOptions<TEntity> {
  filters?: FilterOptions<TEntity>;
}

/**
 * Generic ID collection.
 */
export interface IdentifierCollection {
  ids: readonly EntityIdentifier[];
}