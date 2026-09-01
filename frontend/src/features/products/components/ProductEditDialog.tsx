import {
  useEffect,
} from "react";

import {
  Controller,
  useForm,
} from "react-hook-form";

import {
  Loader2,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";

import {
  CountrySelect,
} from "@/components/ui/country-select";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  Input,
} from "@/components/ui/input";

import {
  Label,
} from "@/components/ui/label";

import {
  Textarea,
} from "@/components/ui/textarea";

import {
  useProductTaxCodes,
} from "@/hooks/queries/products";

import type {
  Product,
} from "@/types/entities";

import type {
  UpdateProductRequest,
} from "@/types/requests";

import {
  canonicalCountryName,
} from "@/lib/countries";


interface ProductEditDialogProps {
  open: boolean;
  product: Product | null;
  isSubmitting: boolean;
  errorMessage?: string | null;
  onOpenChange: (open: boolean) => void;
  onSubmit: (
    productId: string,
    payload: UpdateProductRequest,
  ) => void;
}


interface ProductEditValues {
  supplier_sku: string;
  name: string;
  generic_name: string;
  description: string;

  requires_prescription: boolean;
  allow_negative_stock: boolean;

  reorder_level: string;
  reorder_qty: string;

  min_sale_price: string;
  default_sale_price: string;
  cost_price: string;

  tax_code: string;

  pack_size: string;
  manufacturer: string;
  country_of_origin: string;
  image_url: string;
}


function nullableString(
  value: string,
): string | null {
  const normalized = value.trim();

  return normalized.length > 0
    ? normalized
    : null;
}


function requiredString(
  value: string,
): string {
  return value.trim();
}


function numericValue(
  value: string,
): string | null {
  const normalized = value.trim();

  return normalized.length > 0
    ? normalized
    : null;
}


export function ProductEditDialog({
  open,
  product,
  isSubmitting,
  errorMessage,
  onOpenChange,
  onSubmit,
}: ProductEditDialogProps) {
  const taxCodesQuery = useProductTaxCodes();

  const {
    control,
    register,
    handleSubmit,
    reset,
  } = useForm<ProductEditValues>({
    defaultValues: {
      supplier_sku: "",
      name: "",
      generic_name: "",
      description: "",

      requires_prescription: false,
      allow_negative_stock: false,

      reorder_level: "",
      reorder_qty: "",

      min_sale_price: "",
      default_sale_price: "",
      cost_price: "",

      tax_code: "",

      pack_size: "",
      manufacturer: "",
      country_of_origin: "",
      image_url: "",
    },
  });

  useEffect(() => {
    if (!product) {
      return;
    }

    reset({
      supplier_sku:
        product.supplier_sku ?? "",

      name:
        product.name ?? "",

      generic_name:
        product.generic_name ?? "",

      description:
        product.description ?? "",

      requires_prescription:
        product.requires_prescription,

      allow_negative_stock:
        product.allow_negative_stock,

      reorder_level:
        product.reorder_level != null
          ? String(product.reorder_level)
          : "",

      reorder_qty:
        product.reorder_qty != null
          ? String(product.reorder_qty)
          : "",

      min_sale_price:
        product.min_sale_price != null
          ? String(product.min_sale_price)
          : "",

      default_sale_price:
        product.default_sale_price != null
          ? String(product.default_sale_price)
          : "",

      cost_price:
        product.cost_price != null
          ? String(product.cost_price)
          : "",

      tax_code:
        product.tax_code ?? "",

      pack_size:
        product.pack_size ?? "",

      manufacturer:
        product.manufacturer ?? "",

      country_of_origin:
        canonicalCountryName(
          product.country_of_origin,
        ),

      image_url:
        product.image_url ?? "",
    });
  }, [
    product,
    reset,
  ]);

  const submit = (
    values: ProductEditValues,
  ) => {
    if (!product) {
      return;
    }

    const name = requiredString(
      values.name,
    );

    if (!name) {
      return;
    }

    const payload: UpdateProductRequest = {
      supplier_sku:
        nullableString(values.supplier_sku),

      name,

      generic_name:
        nullableString(values.generic_name),

      description:
        nullableString(values.description),

      requires_prescription:
        values.requires_prescription,

      allow_negative_stock:
        values.allow_negative_stock,

      reorder_level:
        numericValue(values.reorder_level) ?? "0",

      reorder_qty:
        numericValue(values.reorder_qty) ?? "0",

      min_sale_price:
        numericValue(values.min_sale_price),

      default_sale_price:
        numericValue(values.default_sale_price),

      cost_price:
        numericValue(values.cost_price),

      tax_code:
        nullableString(values.tax_code),

      pack_size:
        nullableString(values.pack_size),

      manufacturer:
        nullableString(values.manufacturer),

      country_of_origin:
        nullableString(
          canonicalCountryName(
            values.country_of_origin,
          ),
        ),

      image_url:
        nullableString(values.image_url),
    };

    onSubmit(
      product.id,
      payload,
    );
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            Edit Product
          </DialogTitle>

          <DialogDescription>
            Update approved product master-data.
            Product identity, units, codes,
            inventory configuration and lifecycle
            state are managed separately.
          </DialogDescription>
        </DialogHeader>

        <form
          id="product-edit-form"
          className="space-y-6"
          onSubmit={handleSubmit(submit)}
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="edit-name">
                Product Name
              </Label>

              <Input
                id="edit-name"
                disabled={isSubmitting}
                {...register(
                  "name",
                  {
                    required:
                      "Product name is required.",
                  },
                )}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-supplier-sku">
                Supplier SKU
              </Label>

              <Input
                id="edit-supplier-sku"
                disabled={isSubmitting}
                {...register("supplier_sku")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-generic-name">
                Generic Name
              </Label>

              <Input
                id="edit-generic-name"
                disabled={isSubmitting}
                {...register("generic_name")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-pack-size">
                Pack Size
              </Label>

              <Input
                id="edit-pack-size"
                disabled={isSubmitting}
                {...register("pack_size")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-manufacturer">
                Manufacturer
              </Label>

              <Input
                id="edit-manufacturer"
                disabled={isSubmitting}
                {...register("manufacturer")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-country-origin">
                Country of Origin
              </Label>

              <Controller
                control={control}
                name="country_of_origin"
                render={({ field }) => (
                  <CountrySelect
                    id="edit-country-origin"
                    value={field.value}
                    onValueChange={field.onChange}
                    onBlur={field.onBlur}
                    disabled={isSubmitting}
                    placeholder="Select country of origin"
                  />
                )}
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="edit-sale-price">
                Selling Price
              </Label>

              <Input
                id="edit-sale-price"
                inputMode="decimal"
                disabled={isSubmitting}
                {...register(
                  "default_sale_price",
                )}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-min-price">
                Minimum Sale Price
              </Label>

              <Input
                id="edit-min-price"
                inputMode="decimal"
                disabled={isSubmitting}
                {...register(
                  "min_sale_price",
                )}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-cost-price">
                Cost Price
              </Label>

              <Input
                id="edit-cost-price"
                inputMode="decimal"
                disabled={isSubmitting}
                {...register("cost_price")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-reorder-level">
                Reorder Level
              </Label>

              <Input
                id="edit-reorder-level"
                inputMode="decimal"
                disabled={isSubmitting}
                {...register("reorder_level")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-reorder-qty">
                Reorder Quantity
              </Label>

              <Input
                id="edit-reorder-qty"
                inputMode="decimal"
                disabled={isSubmitting}
                {...register("reorder_qty")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-tax-code">
                Tax Classification
              </Label>

              <select
                id="edit-tax-code"
                disabled={
                  isSubmitting ||
                  taxCodesQuery.isLoading
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
                {...register("tax_code")}
              >
                <option value="">
                  {taxCodesQuery.isLoading
                    ? "Loading tax classifications..."
                    : "No tax classification"}
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

              {taxCodesQuery.isError ? (
                <p className="text-xs text-destructive">
                  Unable to load tax classifications.
                </p>
              ) : null}
            </div>
          </div>

          <div className="grid gap-3 rounded-lg border p-4 sm:grid-cols-2">
            <label className="flex items-center gap-3 text-sm">
              <input
                type="checkbox"
                className="size-4 rounded border-input"
                disabled={isSubmitting}
                {...register(
                  "requires_prescription",
                )}
              />

              Requires prescription
            </label>

            <label className="flex items-center gap-3 text-sm">
              <input
                type="checkbox"
                className="size-4 rounded border-input"
                disabled={isSubmitting}
                {...register(
                  "allow_negative_stock",
                )}
              />

              Allow selling when stock is unavailable
            </label>
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-description">
              Description
            </Label>

            <Textarea
              id="edit-description"
              disabled={isSubmitting}
              {...register("description")}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-image-url">
              Image URL
            </Label>

            <Input
              id="edit-image-url"
              autoComplete="url"
              disabled={isSubmitting}
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
            onClick={() =>
              onOpenChange(false)
            }
          >
            Cancel
          </Button>

          <Button
            type="submit"
            form="product-edit-form"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 className="animate-spin" />
            ) : null}

            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}


export default ProductEditDialog;
