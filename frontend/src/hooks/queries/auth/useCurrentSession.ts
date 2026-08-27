/**
 * ============================================================================
 * Hela360 Enterprise Current Session Query
 * ============================================================================
 */

import { useQuery } from "@tanstack/react-query";

import { createQueryOptions } from "@/lib/queryFactory";
import QUERY_KEYS from "@/lib/queryKeys";
import { authService } from "@/services/auth";

export function useCurrentSession() {
  return useQuery(
    createQueryOptions(
      QUERY_KEYS.auth.currentSession(),
      () => authService.getCurrentSession(),
    ),
  );
}

export default useCurrentSession;
