import {
  Archive,
  Eye,
  Pencil,
  RotateCcw,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Product } from "@/types/entities";


interface ProductsTableProps {
  products: Product[];
  canEdit: boolean;
  canDelete: boolean;
  onView: (product: Product) => void;
  onEdit: (product: Product) => void;
  onLifecycle: (product: Product) => void;
  onDelete: (product: Product) => void;
}


export function ProductsTable({
  products,
  canEdit,
  canDelete,
  onView,
  onEdit,
  onLifecycle,
  onDelete,
}: ProductsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead>Internal SKU</TableHead>
          <TableHead>Supplier SKU</TableHead>
          <TableHead>Category</TableHead>
          <TableHead>Brand</TableHead>
          <TableHead>Unit</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Selling Price</TableHead>
          <TableHead>Tax</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">
            Actions
          </TableHead>
        </TableRow>
      </TableHeader>

      <TableBody>
        {products.map((product) => (
          <TableRow key={product.id}>
            <TableCell>
              <div className="min-w-52">
                <p className="font-medium">
                  {product.name}
                </p>

                <p className="text-xs text-muted-foreground">
                  {product.generic_name ??
                    product.manufacturer ??
                    "No generic name recorded"}
                </p>
              </div>
            </TableCell>

            <TableCell>
              {product.internal_sku}
            </TableCell>

            <TableCell>
              {product.supplier_sku ??
                "Not provided"}
            </TableCell>

            <TableCell>
              {product.category?.name ??
                "Uncategorized"}
            </TableCell>

            <TableCell>
              {product.brand?.name ??
                "Not provided"}
            </TableCell>

            <TableCell>
              {product.unit?.code ??
                "Not provided"}
            </TableCell>

            <TableCell>
              {product.product_type}
            </TableCell>

            <TableCell>
              {product.default_sale_price ??
                "Not set"}
            </TableCell>

            <TableCell>
              {product.tax_code ?? "Not set"}
            </TableCell>

            <TableCell>
              <div className="flex flex-wrap gap-1">
                <Badge
                  variant={
                    product.is_active
                      ? "secondary"
                      : "outline"
                  }
                >
                  {product.is_active
                    ? "Active"
                    : "Archived"}
                </Badge>

                {product.requires_prescription ? (
                  <Badge variant="outline">
                    Rx
                  </Badge>
                ) : null}

              </div>
            </TableCell>

            <TableCell>
              <div className="flex justify-end gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  title="View product"
                  onClick={() => onView(product)}
                >
                  <Eye />
                  <span className="sr-only">
                    View product
                  </span>
                </Button>

                {canEdit ? (
                  <>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      title="Edit product"
                      onClick={() =>
                        onEdit(product)
                      }
                    >
                      <Pencil />
                      <span className="sr-only">
                        Edit product
                      </span>
                    </Button>

                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      title={
                        product.is_active
                          ? "Archive product"
                          : "Restore product"
                      }
                      onClick={() =>
                        onLifecycle(product)
                      }
                    >
                      {product.is_active ? (
                        <Archive />
                      ) : (
                        <RotateCcw />
                      )}

                      <span className="sr-only">
                        {product.is_active
                          ? "Archive product"
                          : "Restore product"}
                      </span>
                    </Button>
                  </>
                ) : null}

                {canDelete && !product.is_active ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    title="Permanently delete product"
                    onClick={() =>
                      onDelete(product)
                    }
                  >
                    <Trash2 className="text-destructive" />

                    <span className="sr-only">
                      Permanently delete product
                    </span>
                  </Button>
                ) : null}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}


export default ProductsTable;
