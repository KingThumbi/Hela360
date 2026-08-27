import type {
  GoodsReceiptSupplier,
  GoodsReceiptUser,
  GoodsReceiptWarehouse,
} from "@/types/entities";

export interface GoodsReceiptSummary {
  id: string;

  receipt_number: string;

  received_at: string | null;

  status: "received";

  warehouse: GoodsReceiptWarehouse;

  supplier: GoodsReceiptSupplier | null;

  supplier_reference: string | null;

  item_count: number;

  total_cost: string;

  received_by: GoodsReceiptUser | null;

  created_at: string | null;

  updated_at: string | null;
}
