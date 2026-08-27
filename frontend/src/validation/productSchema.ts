import { z } from "zod";

const optionalDecimalInput = (message: string) =>
  z
    .string()
    .trim()
    .refine(
      (value) => {
        if (value.length === 0) {
          return true;
        }

        const parsed = Number(value);

        return (
          Number.isFinite(parsed) &&
          parsed >= 0
        );
      },
      message,
    );

export const productFormSchema = z.object({
  internal_sku: z
    .string()
    .trim(),

  name: z
    .string()
    .trim()
    .min(1, "Product name is required."),

  supplier_sku: z.string().trim(),
  generic_name: z.string().trim(),
  description: z.string().trim(),
  category_name: z.string().trim(),
  brand_name: z.string().trim(),
  unit_code: z.string().trim(),
  unit_name: z.string().trim(),
  product_type: z.string().trim(),
  track_inventory: z.boolean(),
  track_batches: z.boolean(),
  track_expiry: z.boolean(),
  requires_prescription: z.boolean(),
  allow_negative_stock: z.boolean(),
  reorder_level: optionalDecimalInput(
    "Reorder level must be non-negative.",
  ),
  reorder_qty: optionalDecimalInput(
    "Reorder quantity must be non-negative.",
  ),
  min_sale_price: optionalDecimalInput(
    "Minimum sale price must be non-negative.",
  ),
  default_sale_price: optionalDecimalInput(
    "Selling price must be non-negative.",
  ),
  cost_price: optionalDecimalInput(
    "Cost price must be non-negative.",
  ),
  tax_code: z.string().trim(),
  pack_size: z.string().trim(),
  manufacturer: z.string().trim(),
  country_of_origin: z.string().trim(),
  image_url: z.string().trim(),
  code_type: z.string().trim(),
  code_value: z.string().trim(),
  code_is_primary: z.boolean(),
});

export type ProductFormValues = z.infer<
  typeof productFormSchema
>;
