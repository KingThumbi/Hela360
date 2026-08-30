import {
  Eye,
  Plus,
} from "lucide-react";

import {
  Badge,
} from "@/components/ui/badge";

import {
  Button,
} from "@/components/ui/button";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import type {
  CatalogueItem,
} from "@/types/entities";


interface CatalogueItemsTableProps {
  items: CatalogueItem[];

  canCreate: boolean;

  onAdopt: (
    item: CatalogueItem,
  ) => void;

  onViewProduct: (
    item: CatalogueItem,
  ) => void;
}


function itemDetails(
  item: CatalogueItem,
): string {
  return [
    item.generic_name,
    item.strength,
    item.dosage_form,
  ]
    .filter(Boolean)
    .join(" · ");
}


function packDescription(
  item: CatalogueItem,
): string {
  const quantity =
    item.pack_quantity?.trim();

  const unit =
    item.pack_unit?.trim();

  const type =
    item.pack_type?.trim();

  const primary =
    [quantity, unit]
      .filter(Boolean)
      .join(" ");

  return [primary, type]
    .filter(Boolean)
    .join(" · ") || "Not specified";
}


export function CatalogueItemsTable({
  items,
  canCreate,
  onAdopt,
  onViewProduct,
}: CatalogueItemsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>
            Catalogue Item
          </TableHead>

          <TableHead>
            Brand
          </TableHead>

          <TableHead>
            Category
          </TableHead>

          <TableHead>
            Pack
          </TableHead>

          <TableHead>
            Manufacturer
          </TableHead>

          <TableHead>
            Status
          </TableHead>

          <TableHead className="text-right">
            Action
          </TableHead>
        </TableRow>
      </TableHeader>

      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell>
              <div className="min-w-64">
                <p className="font-medium">
                  {item.canonical_name}
                </p>

                <p className="text-xs text-muted-foreground">
                  {itemDetails(item) ||
                    item.master_code}
                </p>

                {item.requires_prescription ===
                true ? (
                  <Badge
                    variant="outline"
                    className="mt-1"
                  >
                    Rx
                  </Badge>
                ) : null}
              </div>
            </TableCell>

            <TableCell>
              {item.brand_name ??
                "Not specified"}
            </TableCell>

            <TableCell>
              {item.category_name ??
                "Uncategorized"}
            </TableCell>

            <TableCell>
              {packDescription(item)}
            </TableCell>

            <TableCell>
              {item.manufacturer ??
                "Not specified"}
            </TableCell>

            <TableCell>
              <Badge
                variant={
                  item.adoption.is_adopted
                    ? "secondary"
                    : "outline"
                }
              >
                {item.adoption.is_adopted
                  ? "Already in catalogue"
                  : "Available"}
              </Badge>
            </TableCell>

            <TableCell>
              <div className="flex justify-end">
                {item.adoption.is_adopted ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={
                      !item.adoption.product_id
                    }
                    onClick={() =>
                      onViewProduct(item)
                    }
                  >
                    <Eye />
                    View Product
                  </Button>
                ) : canCreate ? (
                  <Button
                    type="button"
                    size="sm"
                    onClick={() =>
                      onAdopt(item)
                    }
                  >
                    <Plus />
                    Add to Products
                  </Button>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    View only
                  </span>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}


export default CatalogueItemsTable;
