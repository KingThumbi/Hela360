import {
  Badge,
} from "@/components/ui/badge";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import type {
  OfficeMasterItem,
} from "@/types/officeCatalogue";


interface MasterItemsTableProps {
  items: OfficeMasterItem[];
}


function itemDetails(
  item: OfficeMasterItem,
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
  item: OfficeMasterItem,
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


function reviewStatusLabel(
  status: string,
): string {
  return status
    .replace(/[_-]+/g, " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}


export function MasterItemsTable({
  items,
}: MasterItemsTableProps) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              Master Item
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
              Review
            </TableHead>

            <TableHead>
              Lifecycle
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

                  <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                    {item.master_code}
                  </p>
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
                <Badge variant="outline">
                  {reviewStatusLabel(
                    item.review_status,
                  )}
                </Badge>
              </TableCell>

              <TableCell>
                <Badge
                  variant={
                    item.is_active
                      ? "secondary"
                      : "outline"
                  }
                >
                  {item.is_active
                    ? "Active"
                    : "Inactive"}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}


export default MasterItemsTable;
