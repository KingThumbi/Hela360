/**
 * ============================================================================
 * Hela360 Frontend
 * Shared Service Types
 * ============================================================================
 *
 * Shared primitive types used throughout the service layer.
 * These types are intentionally lightweight and contain no HTTP concerns.
 */

export type EntityIdentifier = string | number;

export type Primitive =
  | string
  | number
  | boolean
  | bigint
  | symbol
  | null
  | undefined;

export type Nullable<T> = T | null;

export type Optional<T> = T | undefined;

export type Maybe<T> = Nullable<T> | Optional<T>;