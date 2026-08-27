/**
 * ============================================================================
 * Hela360 Product Query Hooks
 * ============================================================================
 *
 * Central export surface for all product-related query hooks.
 *
 * This module provides the complete query and mutation interface for the
 * Products domain.
 *
 * ============================================================================
 */

export {
  useProducts,
} from "./useProducts";

export {
  useProduct,
} from "./useProduct";

export {
  useCreateProduct,
} from "./useCreateProduct";

export {
  useProductByCode,
} from "./useProductByCode";
export {
  useProductUnits,
} from "./useProductUnits";
export {
  useProductTaxCodes,
} from "./useProductTaxCodes";

export {
  useUpdateProduct,
} from "./useUpdateProduct";

export {
  useArchiveProduct,
} from "./useArchiveProduct";

export {
  useRestoreProduct,
} from "./useRestoreProduct";

export {
  useDeleteProduct,
} from "./useDeleteProduct";
