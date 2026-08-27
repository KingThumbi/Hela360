/**
 * ============================================================================
 * Hela360 Update Customer Request
 * ============================================================================
 *
 * The current backend Customer API does not expose a verified update route.
 * This type preserves the existing frontend update-hook contract while keeping
 * ownership under src/types instead of the Customer service.
 *
 * ============================================================================
 */

import type {
  CreateCustomerRequest,
} from "./create-customer-request";

export type UpdateCustomerRequest =
  Partial<CreateCustomerRequest>;
