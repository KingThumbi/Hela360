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
  OfficeMasterItemSupplierEvidence,
  OfficeSupplierMappingEvidence,
  OfficeSupplierPriceEvidence,
} from "@/types/officeCatalogue";


interface MasterItemSupplierEvidenceProps {
  evidence: OfficeMasterItemSupplierEvidence;
}


function money(
  value: string,
  currency: string,
): string {
  const normalized = Number(value);

  const amount =
    Number.isFinite(normalized)
      ? normalized.toLocaleString(
          undefined,
          {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          },
        )
      : value;

  return `${currency} ${amount}`;
}


function dateLabel(
  value: string | null,
): string {
  if (!value) {
    return "Unknown";
  }

  return new Date(
    `${value}T00:00:00`,
  ).toLocaleDateString();
}


function discountLabel(
  value: string | null,
): string {
  if (!value) {
    return "None";
  }

  const normalized =
    Number(value);

  if (!Number.isFinite(normalized)) {
    return `${value}%`;
  }

  return `${normalized.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 4,
    },
  )}%`;
}


export function MasterItemSupplierEvidence({
  evidence,
}: MasterItemSupplierEvidenceProps) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <SummaryBlock
          label="Supplier Listings"
          value={evidence.mapping_count}
        />

        <SummaryBlock
          label="Price Observations"
          value={
            evidence.price_observation_count
          }
        />

        <SummaryBlock
          label="Comparable Prices"
          value={
            evidence.comparable_observation_count
          }
        />
      </div>

      {evidence.mappings.map(
        (mapping) => (
          <SupplierMappingBlock
            key={mapping.id}
            mapping={mapping}
          />
        ),
      )}
    </div>
  );
}


function SupplierMappingBlock({
  mapping,
}: {
  mapping: OfficeSupplierMappingEvidence;
}) {
  const latest =
    mapping.latest_comparable_price;

  return (
    <div className="space-y-4 rounded-md border p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-medium">
              {mapping.supplier.name}
            </h3>

            <Badge
              variant={
                mapping.is_active
                  ? "secondary"
                  : "outline"
              }
            >
              {mapping.is_active
                ? "Active mapping"
                : "Inactive mapping"}
            </Badge>
          </div>

          <p className="mt-1 text-sm text-muted-foreground">
            {mapping.supplier_item_name}
          </p>

          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {mapping.supplier_item_code ??
              "No supplier item code"}
          </p>
        </div>

        <div className="min-w-52 rounded-md border p-3">
          <div className="text-xs uppercase text-muted-foreground">
            Latest Comparable Price
          </div>

          {latest ? (
            <>
              <div className="mt-1 text-lg font-semibold">
                {money(
                  latest.amount,
                  latest.currency,
                )}
              </div>

              <div className="text-xs text-muted-foreground">
                {latest.price_type} ·{" "}
                {dateLabel(
                  latest.effective_date,
                )}
              </div>
            </>
          ) : (
            <div className="mt-1 text-sm text-muted-foreground">
              No dated comparable price
            </div>
          )}
        </div>
      </div>

      {mapping.source_description ? (
        <div className="text-sm text-muted-foreground">
          {mapping.source_description}
        </div>
      ) : null}

      <PriceHistoryTable
        prices={mapping.prices}
      />
    </div>
  );
}


function PriceHistoryTable({
  prices,
}: {
  prices: OfficeSupplierPriceEvidence[];
}) {
  if (prices.length === 0) {
    return (
      <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
        No supplier price observations recorded.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              Effective
            </TableHead>

            <TableHead>
              Price
            </TableHead>

            <TableHead>
              Type
            </TableHead>

            <TableHead>
              Discount
            </TableHead>

            <TableHead>
              VAT Source
            </TableHead>

            <TableHead>
              Procurement
            </TableHead>

            <TableHead>
              Source
            </TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {prices.map((price) => (
            <TableRow key={price.id}>
              <TableCell>
                {dateLabel(
                  price.effective_date,
                )}
              </TableCell>

              <TableCell className="font-medium">
                {money(
                  price.amount,
                  price.currency,
                )}
              </TableCell>

              <TableCell>
                {price.price_type}
              </TableCell>

              <TableCell>
                {discountLabel(
                  price.discount_percent,
                )}
              </TableCell>

              <TableCell>
                {price.vat_source ??
                  "Unknown"}
              </TableCell>

              <TableCell>
                <Badge
                  variant={
                    price.is_comparable_procurement
                      ? "secondary"
                      : "outline"
                  }
                >
                  {price.is_comparable_procurement
                    ? "Comparable"
                    : "Evidence only"}
                </Badge>
              </TableCell>

              <TableCell>
                <div className="min-w-48">
                  <div>
                    {price.source_document ??
                      "Unknown source"}
                  </div>

                  <div className="text-xs text-muted-foreground">
                    {price.source_location ??
                      "Location not recorded"}
                  </div>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}


function SummaryBlock({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs uppercase text-muted-foreground">
        {label}
      </div>

      <div className="mt-1 text-xl font-semibold">
        {value.toLocaleString()}
      </div>
    </div>
  );
}


export default MasterItemSupplierEvidence;
