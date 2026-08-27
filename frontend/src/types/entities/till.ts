/**
 * Canonical operational Till entity returned by the backend POS contract.
 */
export interface Till {
  readonly id: string;

  readonly branch_id: string;

  readonly warehouse_id: string | null;

  readonly code: string;

  readonly name: string;

  readonly is_active: boolean;
}
