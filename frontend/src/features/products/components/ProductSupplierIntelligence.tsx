import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { PATHS } from "@/routes/routes";

import type {
  ProductMovementHistoryItem,
  ProductPriceTrendItem,
} from "@/types/responses/product-history";

import {
  ProductSupplierHistoryPanel,
} from "./ProductSupplierHistoryPanel";

type PurchaseEvidence = ProductPriceTrendItem & {
  currency?: string | null;
};

type SupplierGroup = {
  id: string | null;
  name: string;
  receipts: PurchaseEvidence[];
  latest: PurchaseEvidence;
};

type SupplierCostRow = {
  supplierId: string;
  supplierName: string;
  currency: string;
  cost: number;
  receipt: PurchaseEvidence;
};

function numeric(
  value: string | number | null | undefined,
) {
  if (value == null || value === "") {
    return null;
  }

  const parsed = Number(value);

  return Number.isFinite(parsed)
    ? parsed
    : null;
}

function displayNumber(
  value: string | number | null | undefined,
) {
  const parsed = numeric(value);

  if (parsed == null) {
    return "—";
  }

  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 6,
  }).format(parsed);
}

function displayCost(
  value: string | number | null | undefined,
  currency: string | null | undefined,
) {
  const amount = displayNumber(value);

  return currency
    ? `${currency} ${amount}`
    : `Currency not recorded · ${amount}`;
}

function displayDate(
  value: string | null | undefined,
) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function timestamp(
  item: PurchaseEvidence,
) {
  if (!item.occurred_at) {
    return 0;
  }

  const value = new Date(
    item.occurred_at,
  ).getTime();

  return Number.isFinite(value)
    ? value
    : 0;
}

function receiptLink(
  item: PurchaseEvidence,
) {
  return PATHS.INVENTORY.receipt(
    item.source.id,
  );
}

const linkClassName = `
  inline-flex
  h-8
  items-center
  justify-center
  rounded-md
  border
  px-3
  text-sm
  font-medium
  transition-colors
  hover:bg-accent
  hover:text-accent-foreground
`;

export function ProductSupplierIntelligence({
  purchases,
  movements,
}: {
  purchases: ProductPriceTrendItem[];
  movements: ProductMovementHistoryItem[];
}) {
  const evidence =
    purchases as PurchaseEvidence[];

  const supplierMap =
    new Map<string, SupplierGroup>();

  for (const item of evidence) {
    const supplierId =
      item.supplier?.id ?? null;

    const key =
      supplierId ?? "__supplier_unrecorded__";

    const supplierName =
      item.supplier?.name ??
      "Supplier not recorded";

    const existing =
      supplierMap.get(key);

    if (!existing) {
      supplierMap.set(key, {
        id: supplierId,
        name: supplierName,
        receipts: [item],
        latest: item,
      });

      continue;
    }

    existing.receipts.push(item);

    if (
      timestamp(item) >
      timestamp(existing.latest)
    ) {
      existing.latest = item;
    }
  }

  const suppliers = Array.from(
    supplierMap.values(),
  ).sort(
    (left, right) =>
      timestamp(right.latest) -
      timestamp(left.latest),
  );

  /*
   * Compare only each supplier's latest recorded
   * cost within the selected period and currency.
   *
   * Missing supplier IDs or currencies are not
   * suitable for supplier-to-supplier comparison.
   */
  const latestBySupplierCurrency =
    new Map<string, SupplierCostRow>();

  for (const item of evidence) {
    const supplierId =
      item.supplier?.id;

    const supplierName =
      item.supplier?.name;

    const currency =
      item.currency?.trim().toUpperCase();

    const cost = numeric(item.value);

    if (
      !supplierId ||
      !supplierName ||
      !currency ||
      cost == null
    ) {
      continue;
    }

    const key =
      `${currency}::${supplierId}`;

    const existing =
      latestBySupplierCurrency.get(key);

    if (
      !existing ||
      timestamp(item) >
        timestamp(existing.receipt)
    ) {
      latestBySupplierCurrency.set(
        key,
        {
          supplierId,
          supplierName,
          currency,
          cost,
          receipt: item,
        },
      );
    }
  }

  const comparisonByCurrency =
    new Map<
      string,
      SupplierCostRow[]
    >();

  for (
    const row of
    latestBySupplierCurrency.values()
  ) {
    const group =
      comparisonByCurrency.get(
        row.currency,
      ) ?? [];

    group.push(row);

    comparisonByCurrency.set(
      row.currency,
      group,
    );
  }

  const comparisonGroups =
    Array.from(
      comparisonByCurrency.entries(),
    )
      .map(([currency, rows]) => ({
        currency,
        rows: rows.sort(
          (left, right) =>
            left.cost - right.cost,
        ),
      }))
      .sort(
        (left, right) =>
          left.currency.localeCompare(
            right.currency,
          ),
      );

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>
              Supplier intelligence
            </CardTitle>

            <CardDescription>
              Supplier and cost evidence from posted
              Goods Receipts in the selected period.
            </CardDescription>
          </div>

          <Badge variant="outline">
            {suppliers.length} supplier
            {suppliers.length === 1 ? "" : "s"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {suppliers.length === 0 ? (
          <div className="rounded-xl border border-dashed p-8 text-center">
            <p className="font-medium">
              No supplier receipt evidence
            </p>

            <p className="mt-1 text-sm text-muted-foreground">
              No posted Goods Receipt cost evidence
              was found for this product in the
              selected period.
            </p>
          </div>
        ) : (
          <section className="space-y-3">
            <div>
              <h3 className="font-medium">
                Recent suppliers
              </h3>

              <p className="mt-1 text-sm text-muted-foreground">
                Ordered by the latest recorded
                receipt date.
              </p>
            </div>

            <div className="space-y-3">
              {suppliers.map((supplier) => {
                const latest =
                  supplier.latest;

                return (
                  <div
                    key={
                      supplier.id ??
                      "__supplier_unrecorded__"
                    }
                    className="rounded-xl border p-4"
                  >
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-medium">
                            {supplier.name}
                          </p>

                          <Badge variant="outline">
                            {supplier.receipts.length} purchase
                            {supplier.receipts.length === 1
                              ? " entry"
                              : " entries"}
                          </Badge>
                        </div>

                        <p className="text-sm text-muted-foreground">
                          Latest receipt:{" "}
                          {displayDate(
                            latest.occurred_at,
                          )}
                        </p>

                        <p className="text-sm">
                          Latest recorded base-unit cost:{" "}
                          <span className="font-medium">
                            {displayCost(
                              latest.value,
                              latest.currency,
                            )}
                          </span>
                        </p>

                        <p className="text-xs text-muted-foreground">
                          {latest.source.number}
                          {" · "}
                          {latest.warehouse.name}
                        </p>
                      </div>

                      <Link
                        to={receiptLink(latest)}
                        className={linkClassName}
                      >
                        Open Goods Receipt
                      </Link>
                    </div>

                    <ProductSupplierHistoryPanel
                      supplierName={
                        supplier.name
                      }
                      purchases={
                        supplier.receipts
                      }
                      movements={
                        movements
                      }
                    />
                  </div>
                );
              })}
            </div>
          </section>
        )}

        <section className="space-y-3">
          <div>
            <h3 className="font-medium">
              Supplier cost comparison
            </h3>

            <p className="mt-1 text-sm text-muted-foreground">
              Latest recorded base-unit cost per
              supplier, compared only within the
              same receipt currency.
            </p>
          </div>

          {comparisonGroups.length === 0 ? (
            <div className="rounded-xl border border-dashed p-5 text-sm text-muted-foreground">
              No comparable supplier costs are
              available. Comparison requires a
              recorded supplier, cost, and receipt
              currency.
            </div>
          ) : (
            <div className="space-y-4">
              {comparisonGroups.map((group) => {
                const lowestCost =
                  group.rows[0]?.cost ?? null;

                return (
                  <div
                    key={group.currency}
                    className="overflow-hidden rounded-xl border"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b bg-muted/30 px-4 py-3">
                      <p className="font-medium">
                        {group.currency}
                      </p>

                      <p className="text-xs text-muted-foreground">
                        Latest cost per supplier
                      </p>
                    </div>

                    <div className="divide-y">
                      {group.rows.map((row) => {
                        const difference =
                          lowestCost == null
                            ? null
                            : row.cost -
                              lowestCost;

                        const differencePercent =
                          lowestCost != null &&
                          lowestCost > 0 &&
                          difference != null
                            ? (
                                difference /
                                lowestCost
                              ) * 100
                            : null;

                        return (
                          <div
                            key={row.supplierId}
                            className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                          >
                            <div>
                              <p className="font-medium">
                                {row.supplierName}
                              </p>

                              <p className="mt-1 text-xs text-muted-foreground">
                                {displayDate(
                                  row.receipt.occurred_at,
                                )}
                                {" · "}
                                {row.receipt.source.number}
                              </p>
                            </div>

                            <div className="flex flex-wrap items-center gap-3">
                              <div className="text-right">
                                <p className="font-medium">
                                  {displayCost(
                                    row.cost,
                                    row.currency,
                                  )}
                                </p>

                                <p className="text-xs text-muted-foreground">
                                  {difference == null
                                    ? "—"
                                    : `+${displayNumber(
                                        difference,
                                      )} vs lowest`}
                                  {differencePercent != null
                                    ? ` (${displayNumber(
                                        differencePercent,
                                      )}%)`
                                    : ""}
                                </p>
                              </div>

                              <Link
                                to={receiptLink(
                                  row.receipt,
                                )}
                                className={linkClassName}
                              >
                                Receipt
                              </Link>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <p className="text-xs text-muted-foreground">
          Costs come from persisted, posted Goods
          Receipt lines and are normalized to the
          product's base unit. Comparisons use each
          supplier's latest cost in the selected
          period and the same receipt currency.
          They do not account for future quotes,
          payment terms, delivery costs, or other
          commercial factors.
        </p>
      </CardContent>
    </Card>
  );
}

export default ProductSupplierIntelligence;
