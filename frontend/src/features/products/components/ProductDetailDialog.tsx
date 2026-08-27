import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Product } from "@/types/entities";

interface ProductDetailDialogProps {
  open: boolean;
  product: Product | null;
  onOpenChange: (open: boolean) => void;
}

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string | number | boolean | null;
}) {
  return (
    <div className="space-y-1">
      <dt className="text-xs font-medium uppercase text-muted-foreground">
        {label}
      </dt>
      <dd className="text-sm">
        {typeof value === "boolean"
          ? value
            ? "Yes"
            : "No"
          : value ?? "Not provided"}
      </dd>
    </div>
  );
}

export function ProductDetailDialog({
  open,
  product,
  onOpenChange,
}: ProductDetailDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {product?.name ?? "Product"}
          </DialogTitle>
          <DialogDescription>
            Verified product catalogue record.
          </DialogDescription>
        </DialogHeader>

        {product ? (
          <dl className="grid gap-5 md:grid-cols-2">
            <div className="flex flex-wrap gap-2 md:col-span-2">
              <Badge
                variant={
                  product.is_active
                    ? "secondary"
                    : "outline"
                }
              >
                {product.is_active
                  ? "Active"
                  : "Inactive"}
              </Badge>
              {product.requires_prescription ? (
                <Badge variant="outline">
                  Prescription Required
                </Badge>
              ) : null}
              {product.track_inventory ? (
                <Badge variant="outline">
                  Inventory Tracked
                </Badge>
              ) : null}
            </div>

            <DetailItem
              label="Internal SKU"
              value={product.internal_sku}
            />
            <DetailItem
              label="Supplier SKU"
              value={product.supplier_sku}
            />
            <DetailItem
              label="Generic Name"
              value={product.generic_name}
            />
            <DetailItem
              label="Product Type"
              value={product.product_type}
            />
            <DetailItem
              label="Category"
              value={product.category?.name ?? null}
            />
            <DetailItem
              label="Brand"
              value={product.brand?.name ?? null}
            />
            <DetailItem
              label="Unit"
              value={
                product.unit
                  ? `${product.unit.code} - ${product.unit.name}`
                  : null
              }
            />
            <DetailItem
              label="Manufacturer"
              value={product.manufacturer}
            />
            <DetailItem
              label="Pack Size"
              value={product.pack_size}
            />
            <DetailItem
              label="Country of Origin"
              value={product.country_of_origin}
            />
            <DetailItem
              label="Selling Price"
              value={product.default_sale_price}
            />
            <DetailItem
              label="Minimum Sale Price"
              value={product.min_sale_price}
            />
            <DetailItem
              label="Cost Price"
              value={product.cost_price}
            />
            <DetailItem
              label="Tax Code"
              value={product.tax_code}
            />
            <DetailItem
              label="Reorder Level"
              value={product.reorder_level}
            />
            <DetailItem
              label="Reorder Quantity"
              value={product.reorder_qty}
            />
            <DetailItem
              label="Track Batches"
              value={product.track_batches}
            />
            <DetailItem
              label="Track Expiry"
              value={product.track_expiry}
            />
            <DetailItem
              label="Allow Negative Stock"
              value={product.allow_negative_stock}
            />
            <DetailItem
              label="Image URL"
              value={product.image_url}
            />

            <div className="space-y-2 md:col-span-2">
              <dt className="text-xs font-medium uppercase text-muted-foreground">
                Codes
              </dt>
              <dd className="flex flex-wrap gap-2">
                {product.codes.length > 0
                  ? product.codes.map((code) => (
                      <Badge
                        key={code.id}
                        variant="outline"
                      >
                        {code.code_type}:{" "}
                        {code.code_value}
                        {code.is_primary
                          ? " (Primary)"
                          : ""}
                      </Badge>
                    ))
                  : "No codes recorded"}
              </dd>
            </div>

            <div className="space-y-1 md:col-span-2">
              <dt className="text-xs font-medium uppercase text-muted-foreground">
                Description
              </dt>
              <dd className="whitespace-pre-wrap text-sm">
                {product.description ??
                  "Not provided"}
              </dd>
            </div>
          </dl>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
