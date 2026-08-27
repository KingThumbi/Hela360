/**
 * Canonical operational TillShift entity returned by the backend POS
 * lifecycle contract.
 */
export interface TillShift {
  readonly id: string;

  readonly branch_id: string;

  readonly till_id: string;

  readonly cashier_id: string;

  /**
   * True when this shift is controlled by the authenticated session.
   *
   * The backend derives this value from active_session_id without exposing
   * the underlying authentication-session identifier to the frontend.
   */
  readonly owned_by_current_session: boolean;

  readonly status: "open" | "closed" | string;

  readonly opening_float: string;

  readonly closing_cash: string;

  readonly notes: string | null;

  readonly opened_at: string | null;

  readonly closed_at: string | null;

  readonly created_at: string | null;

  readonly updated_at: string | null;
}

export interface TillShiftReconciliation {
  readonly opening_float: string;

  readonly cash_sales_total: string;

  readonly expected_cash: string;

  readonly closing_cash: string;

  readonly cash_difference: string;
}
