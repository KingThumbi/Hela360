/**
 * ============================================================================
 * Hela360 Payment Method Code
 * ============================================================================
 *
 * Payment methods are tenant-owned backend records. The verified Sales checkout
 * route accepts `payment_method_id`, not a finite method enum value.
 */

export type PaymentMethodCode = string;
