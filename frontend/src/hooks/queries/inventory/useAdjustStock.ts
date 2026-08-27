/**
 * ============================================================================
 * Hela360 Adjust Stock Mutation
 * ============================================================================
 *
 * Stock adjustment is not supported by a verified registered backend API.
 *
 * ============================================================================
 */

import {
  useMutation,
} from "@tanstack/react-query";

export function useAdjustStock() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Stock adjustment is not supported by the current backend API.",
        ),
      ),
  });
}

export default useAdjustStock;
