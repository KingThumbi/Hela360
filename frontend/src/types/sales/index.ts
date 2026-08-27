/**
 * Transitional Sales type barrel.
 *
 * Canonical definitions live under `src/types/entities`, `src/types/requests`,
 * `src/types/responses`, and `src/types/enums`.
 */

export type {
  Sale,
  SaleItem,
  SalePayment,
  SaleRefund,
} from "./entities";

export type {
  CreateSaleItemRequest,
  CreateSalePaymentRequest,
  CreateSaleRequest,
  RefundSaleItemRequest,
  RefundSaleRequest,
  UpdateSaleRequest,
} from "./requests";

export {
  SALE_STATUSES,
} from "./enums";
export type {
  PaymentMethodCode,
  SaleStatus,
} from "./enums";
