import {
  Activity,
  Archive,
  Boxes,
  ChevronDown,
  ChevronRight,
  Eye,
  Pencil,
  RotateCcw,
  Trash2,
} from "lucide-react";

import {
  Fragment,
  useState,
} from "react";
import { Link } from "react-router-dom";

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

import { PATHS } from "@/routes/routes";

import {
  ProductIntelligencePreview,
} from "./ProductIntelligencePreview";

import type {
  Product,
} from "@/types/entities";


interface ProductsTableProps {
  products: Product[];
  canEdit: boolean;
  canViewUnits: boolean;
  canDelete: boolean;
  onView: (product: Product) => void;
  onEdit: (product: Product) => void;
  onUnits: (product: Product) => void;
  onLifecycle: (product: Product) => void;
  onDelete: (product: Product) => void;
}


interface ProductActionsProps {
  product: Product;
  canEdit: boolean;
  canViewUnits: boolean;
  canDelete: boolean;
  mobile?: boolean;
  onView: (product: Product) => void;
  onEdit: (product: Product) => void;
  onUnits: (product: Product) => void;
  onLifecycle: (product: Product) => void;
  onDelete: (product: Product) => void;
}


function ProductActions({
  product,
  canEdit,
  canViewUnits,
  canDelete,
  mobile = false,
  onView,
  onEdit,
  onUnits,
  onLifecycle,
  onDelete,
}: ProductActionsProps) {
  if (mobile) {
    return (
      <div className="space-y-2">
          <Link
            to={PATHS.PRODUCTS.detail(product.id)}
            className="
              flex h-8 w-full items-center
              justify-center gap-2 rounded-md
              border bg-background px-3
              text-sm font-medium
              transition-colors
              hover:bg-accent
              hover:text-accent-foreground
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-ring
            "
          >
            <Activity className="size-4" />
            Product Intelligence
          </Link>

        <div className="grid grid-cols-3 gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() =>
              onView(product)
            }
          >
            <Eye />
            View
          </Button>

          {canEdit ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                onEdit(product)
              }
            >
              <Pencil />
              Edit
            </Button>
          ) : (
            <div />
          )}

          {canViewUnits ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                onUnits(product)
              }
            >
              <Boxes />
              Units
            </Button>
          ) : (
            <div />
          )}
        </div>

        {canEdit ? (
          <Button
            type="button"
            variant={
              product.is_active
                ? "outline"
                : "secondary"
            }
            size="sm"
            className="w-full"
            onClick={() =>
              onLifecycle(product)
            }
          >
            {product.is_active ? (
              <Archive />
            ) : (
              <RotateCcw />
            )}

            {product.is_active
              ? "Archive Product"
              : "Restore Product"}
          </Button>
        ) : null}

        {canDelete &&
        !product.is_active ? (
          <Button
            type="button"
            variant="destructive"
            size="sm"
            className="w-full"
            onClick={() =>
              onDelete(product)
            }
          >
            <Trash2 />
            Permanently Delete
          </Button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex justify-end gap-1">
        <Link
          to={PATHS.PRODUCTS.detail(product.id)}
          title="Product Intelligence"
          className="
            inline-flex size-8 items-center
            justify-center rounded-md
            transition-colors
            hover:bg-accent
            hover:text-accent-foreground
            focus-visible:outline-none
            focus-visible:ring-2
            focus-visible:ring-ring
          "
        >
          <Activity className="size-4" />
          <span className="sr-only">
            Product Intelligence
          </span>
        </Link>

      <Button
        type="button"
        variant="ghost"
        size="icon-sm"
        title="View product"
        onClick={() =>
          onView(product)
        }
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

      {canViewUnits ? (
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          title="Units & pack sizes"
          onClick={() =>
            onUnits(product)
          }
        >
          <Boxes />

          <span className="sr-only">
            Units & pack sizes
          </span>
        </Button>
      ) : null}

      {canDelete &&
      !product.is_active ? (
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
  );
}


function ProductMobileCard({
  product,
  canEdit,
  canViewUnits,
  canDelete,
  onView,
  onEdit,
  onUnits,
  onLifecycle,
  onDelete,
}: ProductActionsProps) {
  const [
    intelligenceOpen,
    setIntelligenceOpen,
  ] = useState(false);

  return (
    <article className="rounded-xl border bg-background p-4 shadow-sm">
      <button
        type="button"
        className="
          block
          w-full
          text-left
          outline-none
          focus-visible:rounded-md
          focus-visible:ring-2
          focus-visible:ring-ring
        "
        onClick={() =>
          onView(product)
        }
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="truncate font-semibold">
              {product.name}
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              {product.internal_sku}

              {product.unit?.code
                ? ` · ${product.unit.code}`
                : ""}
            </p>

            {product.generic_name ? (
              <p className="mt-1 truncate text-xs text-muted-foreground">
                {product.generic_name}
              </p>
            ) : null}
          </div>

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
        </div>
      </button>

      <div className="my-4 grid grid-cols-2 gap-3 rounded-lg bg-muted/30 p-3">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Selling Price
          </p>

          <p className="mt-1 text-sm font-semibold">
            {product.default_sale_price ??
              "Not set"}
          </p>
        </div>

        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Category
          </p>

          <p className="mt-1 truncate text-sm">
            {product.category?.name ??
              "Uncategorized"}
          </p>
        </div>

        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Unit
          </p>

          <p className="mt-1 text-sm">
            {product.unit?.code ??
              "Not provided"}
          </p>
        </div>

        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Tax
          </p>

          <p className="mt-1 text-sm">
            {product.tax_code ??
              "Not set"}
          </p>
        </div>
      </div>

      {product.supplier_sku ? (
        <p className="mb-3 truncate text-xs text-muted-foreground">
          Supplier SKU:{" "}
          {product.supplier_sku}
        </p>
      ) : null}

      {product.requires_prescription ? (
        <div className="mb-3">
          <Badge variant="outline">
            Prescription Required
          </Badge>
        </div>
      ) : null}

      <div className="mb-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="w-full justify-between"
          aria-expanded={intelligenceOpen}
          onClick={() =>
            setIntelligenceOpen(
              (current) => !current,
            )
          }
        >
          <span className="flex items-center gap-2">
            <Activity className="size-4" />
            Quick Intelligence
          </span>

          {intelligenceOpen ? (
            <ChevronDown className="size-4" />
          ) : (
            <ChevronRight className="size-4" />
          )}
        </Button>

        {intelligenceOpen ? (
          <div className="mt-3 rounded-xl bg-muted/20 p-3">
            <ProductIntelligencePreview
              product={product}
            />
          </div>
        ) : null}
      </div>

      <ProductActions
        product={product}
        canEdit={canEdit}
        canViewUnits={canViewUnits}
        canDelete={canDelete}
        mobile
        onView={onView}
        onEdit={onEdit}
        onUnits={onUnits}
        onLifecycle={onLifecycle}
        onDelete={onDelete}
      />
    </article>
  );
}


export function ProductsTable({
  products,
  canEdit,
  canViewUnits,
  canDelete,
  onView,
  onEdit,
  onUnits,
  onLifecycle,
  onDelete,
}: ProductsTableProps) {
  const [
    expandedProductId,
    setExpandedProductId,
  ] = useState<string | null>(null);

  return (
    <>
      <div className="space-y-3 p-3 md:hidden">
        {products.map(
          (product) => (
            <ProductMobileCard
              key={product.id}
              product={product}
              canEdit={canEdit}
              canViewUnits={canViewUnits}
              canDelete={canDelete}
              onView={onView}
              onEdit={onEdit}
              onUnits={onUnits}
              onLifecycle={onLifecycle}
              onDelete={onDelete}
            />
          ),
        )}
      </div>

      <div className="hidden md:block">
        <Table className="min-w-[760px]">
          <TableHeader className="bg-muted/50">
            <TableRow className="hover:bg-transparent">
              <TableHead
                className="
                  sticky
                  left-0
                  z-30
                  min-w-[280px]
                  border-r
                  bg-muted
                  shadow-[6px_0_10px_-10px_currentColor]
                "
              >
                Product
              </TableHead>

              <TableHead className="hidden lg:table-cell">
                Category
              </TableHead>

              <TableHead>
                Unit
              </TableHead>

              <TableHead className="whitespace-nowrap">
                Selling Price
              </TableHead>

              <TableHead className="hidden xl:table-cell">
                Tax
              </TableHead>

              <TableHead>
                Status
              </TableHead>

              <TableHead
                className="
                  sticky
                  right-0
                  z-30
                  min-w-[170px]
                  border-l
                  bg-muted
                  text-right
                  shadow-[-6px_0_10px_-10px_currentColor]
                "
              >
                Actions
              </TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {products.map(
              (product) => (
                <Fragment key={product.id}>
                  <TableRow
                  className="
                    group
                    transition-colors
                    hover:bg-muted/40
                  "
                >
                  <TableCell
                    className="
                      sticky
                      left-0
                      z-20
                      border-r
                      bg-background
                      align-top
                      shadow-[6px_0_10px_-10px_currentColor]
                      transition-colors
                      group-hover:bg-muted
                    "
                  >
                    <button
                      type="button"
                      className="
                        block
                        w-full
                        min-w-0
                        text-left
                        outline-none
                        focus-visible:rounded-md
                        focus-visible:ring-2
                        focus-visible:ring-ring
                        focus-visible:ring-offset-2
                      "
                      onClick={() =>
                        onView(product)
                      }
                    >
                      <p className="truncate font-medium text-foreground">
                        {product.name}
                      </p>

                      <p className="mt-1 truncate text-xs text-muted-foreground">
                        {product.internal_sku}

                        {product.unit?.code
                          ? ` · ${product.unit.code}`
                          : ""}
                      </p>

                      <p className="mt-1 truncate text-xs text-muted-foreground">
                        {product.generic_name ??
                          product.manufacturer ??
                          "No generic name recorded"}
                      </p>

                      {product.supplier_sku ? (
                        <p className="mt-1 truncate text-[11px] text-muted-foreground/80">
                          Supplier SKU:{" "}
                          {product.supplier_sku}
                        </p>
                      ) : null}
                    </button>

                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="mt-2 h-7 px-2 text-xs"
                        aria-expanded={
                          expandedProductId ===
                          product.id
                        }
                        onClick={() =>
                          setExpandedProductId(
                            (current) =>
                              current === product.id
                                ? null
                                : product.id,
                          )
                        }
                      >
                        {expandedProductId ===
                        product.id ? (
                          <ChevronDown className="size-3.5" />
                        ) : (
                          <ChevronRight className="size-3.5" />
                        )}
                        Quick Intelligence
                      </Button>
                  </TableCell>

                  <TableCell className="hidden lg:table-cell">
                    {product.category?.name ??
                      "Uncategorized"}
                  </TableCell>

                  <TableCell>
                    <span className="whitespace-nowrap">
                      {product.unit?.code ??
                        "Not provided"}
                    </span>
                  </TableCell>

                  <TableCell>
                    <span className="whitespace-nowrap font-medium">
                      {product.default_sale_price ??
                        "Not set"}
                    </span>
                  </TableCell>

                  <TableCell className="hidden xl:table-cell">
                    {product.tax_code ??
                      "Not set"}
                  </TableCell>

                  <TableCell>
                    <div className="flex min-w-[88px] flex-wrap gap-1">
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

                  <TableCell
                    className="
                      sticky
                      right-0
                      z-20
                      border-l
                      bg-background
                      shadow-[-6px_0_10px_-10px_currentColor]
                      transition-colors
                      group-hover:bg-muted
                    "
                  >
                    <ProductActions
                      product={product}
                      canEdit={canEdit}
                      canViewUnits={canViewUnits}
                      canDelete={canDelete}
                      onView={onView}
                      onEdit={onEdit}
                      onUnits={onUnits}
                      onLifecycle={onLifecycle}
                      onDelete={onDelete}
                    />
                  </TableCell>
                  </TableRow>

                  {expandedProductId ===
                  product.id ? (
                    <TableRow className="hover:bg-transparent">
                      <TableCell
                        colSpan={7}
                        className="bg-muted/20 p-4"
                      >
                        <ProductIntelligencePreview
                          product={product}
                        />
                      </TableCell>
                    </TableRow>
                  ) : null}
                  </Fragment>
                ),

            )}
          </TableBody>
        </Table>
      </div>
    </>
  );
}


export default ProductsTable;
