/**
 * ============================================================================
 * Hela360 Update Sale Request
 * ============================================================================
 *
 * The current backend Sales API does not expose a verified update route.
 * This type preserves the existing frontend update-hook contract while keeping
 * ownership under src/types instead of the Sales service.
 *
 * ============================================================================
 */

import type {
  CreateSaleRequest,
} from "./create-sale-request";

export type UpdateSaleRequest =
  Partial<CreateSaleRequest>;
