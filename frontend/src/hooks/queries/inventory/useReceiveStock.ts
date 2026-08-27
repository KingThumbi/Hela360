/**
 * ============================================================================
 * Hela360 Receive Stock Mutation
 * ============================================================================
 *
 * Stock receipt is not supported by a verified registered backend API.
 *
 * ============================================================================
 */

import {
  useMutation,
} from "@tanstack/react-query";

export function useReceiveStock() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Stock receipt is not supported by the current backend API.",
        ),
      ),
  });
}

export default useReceiveStock;
