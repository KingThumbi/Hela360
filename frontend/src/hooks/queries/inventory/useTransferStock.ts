/**
 * ============================================================================
 * Hela360 Transfer Stock Mutation
 * ============================================================================
 *
 * Stock transfer is not supported by a verified registered backend API.
 *
 * ============================================================================
 */

import {
  useMutation,
} from "@tanstack/react-query";

export function useTransferStock() {
  return useMutation({
    mutationFn: (
      _payload: unknown,
    ): Promise<never> =>
      Promise.reject(
        new Error(
          "Stock transfer is not supported by the current backend API.",
        ),
      ),
  });
}

export default useTransferStock;
