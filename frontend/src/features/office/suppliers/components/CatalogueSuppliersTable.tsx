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
  OfficeCatalogueSupplier,
} from "@/types/officeSupplier";


interface CatalogueSuppliersTableProps {
  suppliers: OfficeCatalogueSupplier[];
}


function dateLabel(
  value: string | null,
): string {
  if (!value) {
    return "Not available";
  }

  return new Date(
    `${value}T00:00:00`,
  ).toLocaleDateString();
}


export function CatalogueSuppliersTable({
  suppliers,
}: CatalogueSuppliersTableProps) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              Supplier
            </TableHead>

            <TableHead>
              Mapped Items
            </TableHead>

            <TableHead>
              Observations
            </TableHead>

            <TableHead>
              Comparable
            </TableHead>

            <TableHead>
              Evidence Only
            </TableHead>

            <TableHead>
              Latest Effective
            </TableHead>

            <TableHead>
              Procurement
            </TableHead>

            <TableHead>
              Lifecycle
            </TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {suppliers.map((supplier) => (
            <TableRow key={supplier.id}>
              <TableCell>
                <div className="min-w-52">
                  <p className="font-medium">
                    {supplier.name}
                  </p>

                  <p className="text-xs text-muted-foreground">
                    {supplier.country ??
                      "Country not recorded"}
                  </p>
                </div>
              </TableCell>

              <TableCell>
                {supplier.mapping_count.toLocaleString()}
              </TableCell>

              <TableCell>
                {supplier
                  .price_observation_count
                  .toLocaleString()}
              </TableCell>

              <TableCell>
                {supplier
                  .comparable_observation_count
                  .toLocaleString()}
              </TableCell>

              <TableCell>
                {supplier
                  .non_comparable_observation_count
                  .toLocaleString()}
              </TableCell>

              <TableCell>
                {dateLabel(
                  supplier.latest_effective_date,
                )}
              </TableCell>

              <TableCell>
                <Badge
                  variant={
                    supplier.procurement_comparable
                      ? "secondary"
                      : "outline"
                  }
                >
                  {supplier.procurement_comparable
                    ? "Comparable"
                    : "Evidence only"}
                </Badge>
              </TableCell>

              <TableCell>
                <Badge
                  variant={
                    supplier.is_active
                      ? "secondary"
                      : "outline"
                  }
                >
                  {supplier.is_active
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


export default CatalogueSuppliersTable;
