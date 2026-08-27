import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import {
  Controller,
  useForm,
} from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  useProductTaxCodes,
} from "@/hooks/queries/products";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { CreateProductRequest } from "@/types/requests";
import {
  productFormSchema,
  type ProductFormValues,
} from "@/validation/productSchema";

interface ProductFormDialogProps {
  open: boolean;
  isSubmitting: boolean;
  errorMessage?: string | null;
  onOpenChange: (open: boolean) => void;
  onCreate: (payload: CreateProductRequest) => void;
}

const emptyValues: ProductFormValues = {
  internal_sku: "",
  name: "",
  supplier_sku: "",
  generic_name: "",
  description: "",
  category_name: "",
  brand_name: "",
  unit_code: "",
  unit_name: "",
  product_type: "stockable",
  track_inventory: true,
  track_batches: false,
  track_expiry: false,
  requires_prescription: false,
  allow_negative_stock: false,
  reorder_level: "0",
  reorder_qty: "0",
  min_sale_price: "",
  default_sale_price: "",
  cost_price: "",
  tax_code: "",
  pack_size: "",
  manufacturer: "",
  country_of_origin: "",
  image_url: "",
  code_type: "",
  code_value: "",
  code_is_primary: true,
};

function optionalText(
  value: string,
): string | undefined {
  const trimmed = value.trim();

  return trimmed.length > 0
    ? trimmed
    : undefined;
}

function optionalDecimal(
  value: string,
): string | undefined {
  const trimmed = value.trim();

  return trimmed.length > 0
    ? trimmed
    : undefined;
}

function buildPayload(
  values: ProductFormValues,
): CreateProductRequest {
  const codeType = values.code_type.trim();
  const codeValue = values.code_value.trim();

  return {
    internal_sku: optionalText(
      values.internal_sku,
    ),
    name: values.name.trim(),
    supplier_sku: optionalText(
      values.supplier_sku,
    ),
    generic_name: optionalText(
      values.generic_name,
    ),
    description: optionalText(
      values.description,
    ),
    category_name: optionalText(
      values.category_name,
    ),
    brand_name: optionalText(values.brand_name),
    unit_code: optionalText(values.unit_code),
    unit_name: optionalText(values.unit_name),
    product_type:
      optionalText(values.product_type) ??
      "stockable",
    track_inventory: values.track_inventory,
    track_batches: values.track_batches,
    track_expiry: values.track_expiry,
    requires_prescription:
      values.requires_prescription,
    allow_negative_stock:
      values.allow_negative_stock,
    reorder_level: optionalDecimal(
      values.reorder_level,
    ),
    reorder_qty: optionalDecimal(
      values.reorder_qty,
    ),
    min_sale_price: optionalDecimal(
      values.min_sale_price,
    ),
    default_sale_price: optionalDecimal(
      values.default_sale_price,
    ),
    cost_price: optionalDecimal(
      values.cost_price,
    ),
    tax_code: optionalText(values.tax_code),
    pack_size: optionalText(values.pack_size),
    manufacturer: optionalText(
      values.manufacturer,
    ),
    country_of_origin: optionalText(
      values.country_of_origin,
    ),
    image_url: optionalText(values.image_url),
    codes:
      codeType && codeValue
        ? [
            {
              code_type: codeType,
              code_value: codeValue,
              is_primary:
                values.code_is_primary,
              generated_by_system: false,
            },
          ]
        : undefined,
  };
}

function FieldError({
  message,
}: {
  message?: string;
}) {
  if (!message) {
    return null;
  }

  return (
    <p className="text-xs text-destructive">
      {message}
    </p>
  );
}

export function ProductFormDialog({
  open,
  isSubmitting,
  errorMessage,
  onOpenChange,
  onCreate,
}: ProductFormDialogProps) {
  const {
    control,
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = useForm<ProductFormValues>({
    resolver: zodResolver(productFormSchema),
    defaultValues: emptyValues,
  });

  const taxCodesQuery =
    useProductTaxCodes();

  useEffect(() => {
    if (open) {
      reset(emptyValues);
    }
  }, [
    open,
    reset,
  ]);

  const onSubmit = (
    values: ProductFormValues,
  ) => {
    onCreate(buildPayload(values));
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>
            Create Product
          </DialogTitle>
          <DialogDescription>
            Add a tenant-wide catalogue product.
          </DialogDescription>
        </DialogHeader>

        <form
          id="product-form"
          className="grid gap-6"
          onSubmit={handleSubmit(onSubmit)}
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="internal_sku">
                Internal SKU
              </Label>
              <Input
                id="internal_sku"
                autoComplete="off"
                placeholder="Auto-generated if left blank"
                aria-invalid={
                  errors.internal_sku
                    ? true
                    : undefined
                }
                {...register("internal_sku")}
              />
              <p className="text-xs text-muted-foreground">
                Optional. Hela360 generates the next internal SKU if left blank.
              </p>
              <FieldError
                message={
                  errors.internal_sku?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">
                Product Name
              </Label>
              <Input
                id="name"
                autoComplete="off"
                aria-invalid={
                  errors.name ? true : undefined
                }
                {...register("name")}
              />
              <FieldError
                message={errors.name?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="supplier_sku">
                Supplier SKU
              </Label>
              <Input
                id="supplier_sku"
                autoComplete="off"
                {...register("supplier_sku")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="generic_name">
                Generic Name
              </Label>
              <Input
                id="generic_name"
                autoComplete="off"
                {...register("generic_name")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="product_type">
                Product Type
              </Label>
              <Input
                id="product_type"
                autoComplete="off"
                {...register("product_type")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="manufacturer">
                Manufacturer
              </Label>
              <Input
                id="manufacturer"
                autoComplete="organization"
                {...register("manufacturer")}
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="category_name">
                Category
              </Label>
              <Input
                id="category_name"
                {...register("category_name")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="brand_name">
                Brand
              </Label>
              <Input
                id="brand_name"
                {...register("brand_name")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit_code">
                Unit Code
              </Label>
              <Input
                id="unit_code"
                {...register("unit_code")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit_name">
                Unit Name
              </Label>
              <Input
                id="unit_name"
                {...register("unit_name")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pack_size">
                Pack Size
              </Label>
              <Input
                id="pack_size"
                {...register("pack_size")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="country_of_origin">
                Country of Origin
              </Label>
              <Input
                id="country_of_origin"
                autoComplete="country-name"
                {...register("country_of_origin")}
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="default_sale_price">
                Selling Price
              </Label>
              <Input
                id="default_sale_price"
                inputMode="decimal"
                aria-invalid={
                  errors.default_sale_price
                    ? true
                    : undefined
                }
                {...register(
                  "default_sale_price",
                )}
              />
              <FieldError
                message={
                  errors.default_sale_price
                    ?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="min_sale_price">
                Minimum Sale Price
              </Label>
              <Input
                id="min_sale_price"
                inputMode="decimal"
                aria-invalid={
                  errors.min_sale_price
                    ? true
                    : undefined
                }
                {...register("min_sale_price")}
              />
              <FieldError
                message={
                  errors.min_sale_price?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cost_price">
                Cost Price
              </Label>
              <Input
                id="cost_price"
                inputMode="decimal"
                aria-invalid={
                  errors.cost_price
                    ? true
                    : undefined
                }
                {...register("cost_price")}
              />
              <FieldError
                message={
                  errors.cost_price?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tax_code">
                Tax Classification
              </Label>

              <Controller
                control={control}
                name="tax_code"
                render={({ field }) => (
                  <select
                    id="tax_code"
                    value={field.value}
                    onChange={field.onChange}
                    onBlur={field.onBlur}
                    ref={field.ref}
                    disabled={
                      taxCodesQuery.isLoading ||
                      isSubmitting
                    }
                    aria-invalid={
                      errors.tax_code
                        ? true
                        : undefined
                    }
                    className="
                      h-9
                      w-full
                      rounded-md
                      border
                      border-input
                      bg-background
                      px-3
                      text-sm
                      shadow-xs
                      outline-none
                      focus-visible:border-ring
                      focus-visible:ring-[3px]
                      focus-visible:ring-ring/50
                      disabled:cursor-not-allowed
                      disabled:opacity-50
                    "
                  >
                    <option value="">
                      {
                        taxCodesQuery.isLoading
                          ? "Loading tax classifications..."
                          : "Select tax classification"
                      }
                    </option>

                    {(taxCodesQuery.data ?? []).map(
                      (taxCode) => (
                        <option
                          key={taxCode.id}
                          value={taxCode.code}
                        >
                          {taxCode.code}
                          {" — "}
                          {taxCode.name}
                          {" ("}
                          {Number(
                            taxCode.rate,
                          ).toLocaleString(
                            undefined,
                            {
                              maximumFractionDigits: 4,
                            },
                          )}
                          {"%)"}
                        </option>
                      ),
                    )}
                  </select>
                )}
              />

              {taxCodesQuery.isError ? (
                <p className="text-xs text-destructive">
                  Unable to load tax classifications.
                </p>
              ) : null}

              <FieldError
                message={errors.tax_code?.message}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="reorder_level">
                Reorder Level
              </Label>
              <Input
                id="reorder_level"
                inputMode="decimal"
                aria-invalid={
                  errors.reorder_level
                    ? true
                    : undefined
                }
                {...register("reorder_level")}
              />
              <FieldError
                message={
                  errors.reorder_level?.message
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="reorder_qty">
                Reorder Quantity
              </Label>
              <Input
                id="reorder_qty"
                inputMode="decimal"
                aria-invalid={
                  errors.reorder_qty
                    ? true
                    : undefined
                }
                {...register("reorder_qty")}
              />
              <FieldError
                message={
                  errors.reorder_qty?.message
                }
              />
            </div>
          </div>

          <fieldset className="grid gap-3 rounded-lg border p-4 md:grid-cols-2">
            <legend className="px-1 text-sm font-medium">
              Product Configuration
            </legend>
            {[
              [
                "track_inventory",
                "Track inventory",
              ],
              [
                "track_batches",
                "Track batches",
              ],
              [
                "track_expiry",
                "Track expiry",
              ],
              [
                "requires_prescription",
                "Requires prescription",
              ],
              [
                "allow_negative_stock",
                "Allow negative stock",
              ],
            ].map(([field, label]) => (
              <label
                key={field}
                className="flex items-center gap-2 text-sm"
              >
                <input
                  type="checkbox"
                  className="size-4 rounded border-input"
                  {...register(
                    field as keyof ProductFormValues,
                  )}
                />
                {label}
              </label>
            ))}
          </fieldset>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="code_type">
                Product Code Type
              </Label>
              <Input
                id="code_type"
                placeholder="Barcode, GTIN, QR"
                {...register("code_type")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="code_value">
                Product Code
              </Label>
              <Input
                id="code_value"
                autoComplete="off"
                {...register("code_value")}
              />
            </div>

            <label
              htmlFor="code_is_primary"
              className="flex items-end gap-2 pb-2 text-sm"
            >
              <input
                id="code_is_primary"
                type="checkbox"
                className="size-4 rounded border-input"
                {...register("code_is_primary")}
              />
              Primary code
            </label>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">
              Description
            </Label>
            <Textarea
              id="description"
              {...register("description")}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="image_url">
              Image URL
            </Label>
            <Input
              id="image_url"
              autoComplete="url"
              {...register("image_url")}
            />
          </div>

          {errorMessage ? (
            <p className="text-sm text-destructive">
              {errorMessage}
            </p>
          ) : null}
        </form>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={isSubmitting}
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            form="product-form"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 className="animate-spin" />
            ) : null}
            Create Product
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
