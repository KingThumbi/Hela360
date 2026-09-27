import type { Product, ProductUnit } from "@/types/entities";
import type { PaginationMeta } from "@/types/api";

export interface ProductHistoryCapabilities {
  sales_history: boolean;
  purchase_history: boolean;
  movement_history: boolean;
  stock_history: boolean;
  profitability: boolean;
}

export interface ProductHistoryStockSummary {
  quantity_on_hand?: string;
  quantity_reserved?: string;
  quantity_available?: string;
  [key: string]: unknown;
}

export interface ProductHistoryActivity {
  movement_count: number;
  last_movement_at: string | null;
}

export interface ProductHistorySummary {
  product: Product;
  units: ProductUnit[];
  current_stock: ProductHistoryStockSummary;
  activity: ProductHistoryActivity;
  capabilities: ProductHistoryCapabilities;
}

export interface ProductHistorySummaryResponse {
  ok: true;
  item: ProductHistorySummary;
}

export interface ProductHistoryUom {
  code: string | null;
  name: string | null;
  conversion_factor_to_base: string;
}

export interface ProductHistoryBatch {
  id: string | null;
  batch_number: string | null;
  expiry_date?: string | null;
  manufacture_date?: string | null;
}

export interface ProductSalesHistoryItem {
  sale_item_id: string;

  sale: {
    id: string;
    sale_number: string;
    sale_date: string | null;
    status: string;
    sale_channel: string;
    refund_status: string | null;
    refunded_amount: string;
  };

  warehouse: {
    id: string;
    code: string;
    name: string;
  };

  customer: {
    id: string;
    customer_number: string;
    first_name: string | null;
    last_name: string | null;
    other_names: string | null;
    phone: string | null;
  } | null;

  quantity: string;
  base_quantity: string;

  uom: ProductHistoryUom;

  unit_price: string;
  normalized_base_unit_price: string | null;

  discount_amount: string;
  tax_amount: string;
  line_total: string;

  is_returned: boolean;

  batch: ProductHistoryBatch | null;
}

export interface ProductPurchaseHistoryItem {
  receipt_item_id: string;

  receipt: {
    id: string;
    receipt_number: string;
    status: string;
    received_at: string | null;
    posted_at: string | null;
    supplier_reference: string | null;
    supplier_invoice_number: string | null;
    supplier_invoice_date: string | null;
    invoice_currency: string | null;
  };

  warehouse: {
    id: string;
    code: string;
    name: string;
  };

  supplier: {
    id: string;
    supplier_code: string | null;
    name: string;
  } | null;

  line_number: number;

  quantity: string;
  base_quantity: string;

  uom: ProductHistoryUom;

  unit_cost: string;
  base_unit_cost: string;

  batch: ProductHistoryBatch;
}

export interface ProductMovementHistoryItem {
  id: string;
  movement_type: string;
  quantity: string;
  unit_cost?: string | null;
  unit_price?: string | null;
  sale_item_id?: string | null;

  product?: {
    id: string;
    name?: string | null;
    internal_sku?: string | null;
  } | null;

  warehouse?: {
    id: string;
    code?: string | null;
    name?: string | null;
  } | null;

  batch?: {
    id?: string | null;
    batch_number?: string | null;
  } | null;

  reference?: {
    type?: string | null;
    id?: string | null;
  } | null;

  performed_by?: {
    id?: string | null;
    name?: string | null;
  } | null;

  created_at: string | null;
}

export interface ProductHistoryListResponse<T> {
  ok: true;
  items: T[];
  pagination: PaginationMeta;
}

export interface ProductHistoryListParams {
  page?: number;
  per_page?: number;
  date_from?: string;
  date_to?: string;
  warehouse_id?: string;
}

export interface ProductSalesHistoryParams
  extends ProductHistoryListParams {
  status?: string;
  customer_id?: string;
}

export interface ProductPurchaseHistoryParams
  extends ProductHistoryListParams {
  supplier_id?: string;
}

export interface ProductMovementHistoryParams {
  page?: number;
  per_page?: number;
  warehouse_id?: string;
  movement_type?: string;
  date_from?: string;
  date_to?: string;
}
