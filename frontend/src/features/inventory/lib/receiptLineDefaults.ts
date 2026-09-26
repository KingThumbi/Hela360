export interface ReceiptLineDefaults {
  product_unit_id: string;

  quantity: string;
  invoiced_quantity: string;
  received_quantity: string;
  accepted_quantity: string;
  rejected_quantity: string;
  bonus_quantity: string;

  unit_cost: string;

  batch_number: string;
  manufacture_date: string;
  expiry_date: string;
  supplier_batch_reference: string;

  supplier_item_code: string;
  supplier_description: string;

  supplier_unit_price: string;
  discount_percent: string;
  discount_amount: string;
  tax_rate: string;
  tax_amount: string;
  net_unit_cost: string;
  line_total: string;

  discrepancy_status: string;
  discrepancy_reason: string;
}

/**
 * Initial editable state for a newly added goods-receipt line.
 *
 * Keep this helper free of React and API dependencies so the receiving
 * quantity contract can be regression-tested independently.
 */
export function createReceiptLineDefaults(
  costPrice: string | null | undefined,
): ReceiptLineDefaults {
  return {
    product_unit_id: "",

    // Stock Qty is inventory truth and must be explicitly confirmed.
    // Never manufacture a quantity merely because a product was added.
    quantity: "",

    invoiced_quantity: "",
    received_quantity: "",
    accepted_quantity: "",
    rejected_quantity: "",
    bonus_quantity: "",

    unit_cost: costPrice ?? "0.00",

    batch_number: "",
    manufacture_date: "",
    expiry_date: "",
    supplier_batch_reference: "",

    supplier_item_code: "",
    supplier_description: "",

    supplier_unit_price: "",
    discount_percent: "",
    discount_amount: "",
    tax_rate: "",
    tax_amount: "",
    net_unit_cost: "",
    line_total: "",

    discrepancy_status: "",
    discrepancy_reason: "",
  };
}
