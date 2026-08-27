export interface ProductUnit {
  id: string;
  tenant_id: string;
  product_id: string;
  unit: {
    id: string;
    code: string;
    name: string;
  } | null;
  conversion_factor_to_base: string;
  is_base: boolean;
  can_sell: boolean;
  can_receive: boolean;
  sale_price: string | null;
  minimum_sale_price: string | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}
