/**
 * ============================================================================
 * Hela360 Delete Product Mutation
 * ============================================================================
 *
 * Product delete placeholder.
 *
 * Responsibilities
 * ----------------
 * • Delete products
 * • Invalidate affected caches
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers:
 *
 * • Product Deletion
 * • Bulk Product Management
 * • Product Administration
 *
 * ============================================================================
 */

import {
  useDeleteEntity,
} from "@/hooks/queries/common";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Product deletion is not supported by the verified backend API.
 */
export function useDeleteProduct() {
  return useDeleteEntity(
    async (): Promise<void> => {
      throw new Error(
        "Product deletion is not supported by the current backend API.",
      );
    },
  );
}

export default useDeleteProduct;
