/**
 * ============================================================================
 * Hela360 Enterprise Query Client
 * ============================================================================
 *
 * Centralized TanStack Query configuration.
 *
 * Responsibilities
 * ----------------
 * • Configure query caching
 * • Configure mutation behaviour
 * • Configure retry strategy
 * • Configure garbage collection
 * • Configure stale times
 * • Provide a singleton QueryClient
 *
 * Every query and mutation in the application should use this client.
 *
 * ============================================================================
 */

import {
  MutationCache,
  QueryCache,
  QueryClient,
} from "@tanstack/react-query";

import { AppError } from "@/lib/errors";

/* ============================================================================
 * Configuration
 * ============================================================================
 */

/**
 * Default cache lifetime.
 *
 * Five minutes.
 */
const GC_TIME = 1000 * 60 * 5;

/**
 * Data is considered fresh for one minute.
 */
const STALE_TIME = 1000 * 60;

/**
 * Maximum retry attempts.
 */
const MAX_RETRIES = 1;

/* ============================================================================
 * Retry Strategy
 * ============================================================================
 */

function shouldRetry(
  failureCount: number,
  error: unknown,
): boolean {
  if (failureCount >= MAX_RETRIES) {
    return false;
  }

  if (error instanceof AppError) {
    /**
     * Never retry client-side errors.
     */
    if (
      error.status !== undefined &&
      error.status >= 400 &&
      error.status < 500
    ) {
      return false;
    }
  }

  return true;
}

/* ============================================================================
 * Query Cache
 * ============================================================================
 */

const queryCache = new QueryCache({
  onError(error) {
    /**
     * Future integrations:
     *
     * • Logger
     * • Toast notifications
     * • Sentry
     * • Datadog
     */
    if (import.meta.env.DEV) {
      console.error("Query Error", error);
    }
  },
});

/* ============================================================================
 * Mutation Cache
 * ============================================================================
 */

const mutationCache = new MutationCache({
  onError(error) {
    if (import.meta.env.DEV) {
      console.error("Mutation Error", error);
    }
  },
});

/* ============================================================================
 * Query Client
 * ============================================================================
 */

export const queryClient = new QueryClient({
  queryCache,

  mutationCache,

  defaultOptions: {
    queries: {
      retry: shouldRetry,

      staleTime: STALE_TIME,

      gcTime: GC_TIME,

      refetchOnWindowFocus: false,

      refetchOnReconnect: true,

      refetchOnMount: false,
    },

    mutations: {
      retry: false,
    },
  },
});

export default queryClient;