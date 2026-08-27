/**
 * Canonical operational Warehouse entity returned by the backend POS
 * warehouse-read contract.
 */
export interface Warehouse {
  readonly id: string;

  readonly branch_id: string;

  readonly code: string;

  readonly name: string;

  readonly warehouse_type: string;

  readonly is_active: boolean;
}
