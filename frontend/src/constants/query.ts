/**
 * ============================================================================
 * Hela360 Enterprise React Query Configuration
 * ============================================================================
 *
 * Centralized React Query defaults for the entire application.
 *
 * Responsibilities
 * ----------------
 * • Query caching
 * • Garbage collection
 * • Retry policies
 * • Refetch behaviour
 * • Future polling configuration
 *
 * Components and providers should reference these constants instead of
 * hardcoding React Query options.
 *
 * ============================================================================
 */

export const QUERY = {
  /**
   * --------------------------------------------------------------------------
   * Queries
   * --------------------------------------------------------------------------
   */

  /**
   * Data remains fresh for 5 minutes.
   */
  staleTime: 1000 * 60 * 5,

  /**
   * Remove inactive queries after 30 minutes.
   */
  gcTime: 1000 * 60 * 30,

  /**
   * Retry failed queries once.
   */
  retry: 1,

  /**
   * Refetch behaviour.
   */
  refetchOnWindowFocus: false,

  refetchOnReconnect: true,

  refetchOnMount: true,

  /**
   * --------------------------------------------------------------------------
   * Mutations
   * --------------------------------------------------------------------------
   */

  /**
   * Retry failed mutations once.
   */
  mutationRetry: 1,

  /**
   * --------------------------------------------------------------------------
   * Future Configuration
   * --------------------------------------------------------------------------
   *
   * Reserved for future enterprise features:
   *
   * • Background polling
   * • Offline synchronization
   * • Broadcast cache
   * • Persisted cache
   * • Network mode
   */

  refetchInterval: false as const,

  refetchIntervalInBackground: false,

  networkMode: "online" as const,
} as const;

export default QUERY;