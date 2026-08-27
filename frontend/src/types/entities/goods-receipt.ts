export interface GoodsReceiptWarehouse {
  id: string;

  code: string;

  name: string;
}

export interface GoodsReceiptSupplier {
  id: string;

  supplier_code: string;

  name: string;
}

export interface GoodsReceiptUser {
  id: string;

  name: string | null;

  username: string | null;
}

export interface GoodsReceiptProduct {
  id: string;

  internal_sku: string;

  name: string;
}

export interface GoodsReceiptBatch {
  id: string;

  batch_number: string | null;

  expiry_date: string | null;
}

export interface GoodsReceiptItem {
  id: string;

  line_number: number;

  product: GoodsReceiptProduct;

  quantity: string;

  base_quantity: string;

  product_unit_id: string | null;

  unit_code: string | null;

  unit_name: string | null;

  conversion_factor_to_base: string;

  batch: GoodsReceiptBatch | null;

  batch_number: string | null;

  manufacture_date: string | null;

  expiry_date: string | null;

  unit_cost: string;

  base_unit_cost: string;

  supplier_batch_reference: string | null;
}

export interface GoodsReceipt {
  id: string;

  receipt_number: string;

  warehouse: GoodsReceiptWarehouse;

  supplier: GoodsReceiptSupplier | null;

  supplier_reference: string | null;

  received_at: string | null;

  status: "received";

  notes: string | null;

  received_by: GoodsReceiptUser | null;

  items: GoodsReceiptItem[];

  created_at: string | null;

  updated_at: string | null;
}
