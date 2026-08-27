/**
 * ============================================================================
 * Hela360 Enterprise Query Provider
 * ============================================================================
 *
 * Initializes the application's React Query infrastructure.
 *
 * Responsibilities
 * ----------------
 * • Create the singleton QueryClient
 * • Configure enterprise query defaults
 * • Provide React Query context
 * • Register React Query Devtools
 *
 * All React Query configuration should be centralized here.
 *
 * ============================================================================
 */

import type { PropsWithChildren } from "react";
import { useState } from "react";

import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { QUERY } from "@/constants";

/* ============================================================================
 * Query Provider
 * ============================================================================
 */

export function QueryProvider({
  children,
}: PropsWithChildren) {
  /**
   * Create the QueryClient once.
   *
   * React Query recommends creating exactly one
   * QueryClient for the lifetime of the application.
   */
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: QUERY.staleTime,
            gcTime: QUERY.gcTime,
            retry: QUERY.retry,
            refetchOnWindowFocus:
              QUERY.refetchOnWindowFocus,
            refetchOnReconnect:
              QUERY.refetchOnReconnect,
            refetchOnMount:
              QUERY.refetchOnMount,
          },

          mutations: {
            retry: QUERY.mutationRetry,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}

      {import.meta.env.DEV && (
        <ReactQueryDevtools
          initialIsOpen={false}
        />
      )}
    </QueryClientProvider>
  );
}

export default QueryProvider;