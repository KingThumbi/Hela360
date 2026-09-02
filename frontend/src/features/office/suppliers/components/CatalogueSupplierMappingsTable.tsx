import {
  Link,
} from "react-router-dom";

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

import {
  OFFICE_PATHS,
} from "@/routes/officeRoutes";

import type {
  OfficeCatalogueSupplierMapping,
} from "@/types/officeSupplier";


interface CatalogueSupplierMappingsTableProps {
  mappings: OfficeCatalogueSupplierMapping[];
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


function priceLabel(
  mapping: OfficeCatalogueSupplierMapping,
): string {
  const price =
    mapping.latest_comparable_price;

  if (!price) {
    return "No dated comparable price";
  }

  return [
    price.currency,
    Number(price.amount).toLocaleString(),
  ]
    .filter(Boolean)
    .join(" ");
}


export function CatalogueSupplierMappingsTable({
  mappings,
}: CatalogueSupplierMappingsTableProps) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              Master Item
            </TableHead>

            <TableHead>
              Supplier Listing
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
              Latest Comparable
            </TableHead>

            <TableHead>
              Effective
            </TableHead>

            <TableHead>
              Mapping
            </TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {mappings.map((mapping) => (
            <TableRow key={mapping.id}>
              <TableCell>
                <div className="min-w-64 space-y-1">
                  <Link
                    to={
                      OFFICE_PATHS.CATALOGUE
                        .masterItemDetail(
                          mapping.master_item.id,
                        )
                    }
                    className="font-medium hover:underline"
                  >
                    {
                      mapping.master_item
                        .canonical_name
                    }
                  </Link>

                  <p className="text-xs text-muted-foreground">
                    {
                      mapping.master_item
                        .master_code
                    }
                  </p>

                  <div className="flex gap-2">
                    <Badge variant="outline">
                      {
                        mapping.master_item
                          .review_status
                      }
                    </Badge>

                    <Badge
                      variant={
                        mapping.master_item
                          .is_active
                          ? "secondary"
                          : "outline"
                      }
                    >
                      {
                        mapping.master_item
                          .is_active
                          ? "Active"
                          : "Inactive"
                      }
                    </Badge>
                  </div>
                </div>
              </TableCell>

              <TableCell>
                <div className="min-w-56 space-y-1">
                  <p>
                    {mapping.supplier_item_name}
                  </p>

                  <p className="text-xs text-muted-foreground">
                    {mapping.supplier_item_code ??
                      "No supplier item code"}
                  </p>

                  {mapping.source_description ? (
                    <p className="text-xs text-muted-foreground">
                      {mapping.source_description}
                    </p>
                  ) : null}
                </div>
              </TableCell>

              <TableCell>
                {mapping
                  .price_observation_count
                  .toLocaleString()}
              </TableCell>

              <TableCell>
                {mapping
                  .comparable_observation_count
                  .toLocaleString()}
              </TableCell>

              <TableCell>
                {mapping
                  .non_comparable_observation_count
                  .toLocaleString()}
              </TableCell>

              <TableCell>
                <div className="min-w-44">
                  <p>
                    {priceLabel(mapping)}
                  </p>

                  {mapping.latest_comparable_price ? (
                    <p className="text-xs text-muted-foreground">
                      {
                        mapping
                          .latest_comparable_price
                          .price_type
                      }
                    </p>
                  ) : null}
                </div>
              </TableCell>

              <TableCell>
                {dateLabel(
                  mapping
                    .latest_comparable_price
                    ?.effective_date ??
                    null,
                )}
              </TableCell>

              <TableCell>
                <Badge
                  variant={
                    mapping.is_active
                      ? "secondary"
                      : "outline"
                  }
                >
                  {mapping.is_active
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


export default CatalogueSupplierMappingsTable;
