/**
 * ============================================================================
 * Hela360 Frontend
 * HTTP Request Types
 * ============================================================================
 *
 * Shared request configuration used by BaseService.
 */

import type {
  AxiosRequestConfig,
  GenericAbortSignal,
} from "axios";

/**
 * Standard request configuration accepted by every BaseService method.
 *
 * Extends AxiosRequestConfig while preserving a strongly typed abort signal.
 */
export interface RequestOptions
  extends AxiosRequestConfig {
  signal?: GenericAbortSignal;
}