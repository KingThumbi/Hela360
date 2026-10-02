import {
  ChevronDown,
} from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import {
  CardDescription,
} from "@/components/ui/card";

import { PATHS } from "@/routes/routes";

import type {
  ProductPriceTrendItem,
} from "@/types/responses/product-history";

function numeric(
  value: string | number | null | undefined,
) {
  if (
    value == null ||
    value === ""
  ) {
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
  item: ProductPriceTrendItem,
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

function normalizeCurrency(
  value: string | null | undefined,
) {
  const normalized =
    value?.trim().toUpperCase();

  return normalized || null;
}

function receiptLink(
  item: ProductPriceTrendItem,
) {
  return PATHS.INVENTORY.receipt(
    item.source.id,
  );
}

type CostPoint = {
  id: string;
  date: string;
  cost: number;
  receiptNumber: string;
};

type ReceiptActivityPoint = {
  month: string;
  label: string;
  receiptCount: number;
  baseUnits: number;
};

export function ProductSupplierHistoryPanel({
  supplierName,
  purchases,
}: {
  supplierName: string;
  purchases: ProductPriceTrendItem[];
}) {
  const sortedPurchases = [
    ...purchases,
  ].sort((left, right) => {
    const dateDifference =
      timestamp(right) -
      timestamp(left);

    if (dateDifference !== 0) {
      return dateDifference;
    }

    return right.id.localeCompare(
      left.id,
    );
  });

  const receiptDocumentCount =
    new Set(
      purchases.map(
        (item) =>
          item.source.id,
      ),
    ).size;

  const purchaseEntryCount =
    purchases.length;

  const baseUnitsReceived =
    purchases.reduce(
      (total, item) =>
        total +
        (numeric(item.quantity) ?? 0),
      0,
    );

  const latestReceipt =
    sortedPurchases[0] ?? null;

  const recentEntries =
    sortedPurchases.slice(0, 10);

  const costByCurrency =
    new Map<
      string,
      CostPoint[]
    >();

  for (const item of purchases) {
    const currency =
      normalizeCurrency(
        item.currency,
      );

    const cost =
      numeric(item.value);

    if (
      !currency ||
      cost == null ||
      !item.occurred_at
    ) {
      continue;
    }

    const group =
      costByCurrency.get(
        currency,
      ) ?? [];

    group.push({
      id: item.id,
      date: item.occurred_at,
      cost,
      receiptNumber:
        item.source.number,
    });

    costByCurrency.set(
      currency,
      group,
    );
  }

  const costGroups =
    Array.from(
      costByCurrency.entries(),
    )
      .map(
        ([currency, points]) => ({
          currency,
          points: points.sort(
            (left, right) =>
              new Date(
                left.date,
              ).getTime() -
              new Date(
                right.date,
              ).getTime(),
          ),
        }),
      )
      .sort(
        (left, right) =>
          left.currency.localeCompare(
            right.currency,
          ),
      );

  const costEvidenceWithoutCurrency =
    purchases.filter(
      (item) =>
        numeric(item.value) != null &&
        !normalizeCurrency(
          item.currency,
        ),
    ).length;

  /*
   * Receipt activity is based on unique posted
   * Goods Receipt source documents. Quantity remains
   * line-level because multiple persisted product
   * entries on the same receipt can legitimately
   * contribute to the product total.
   */
  const receiptActivityByMonth =
    new Map<
      string,
      {
        receiptIds: Set<string>;
        baseUnits: number;
      }
    >();

  for (const item of purchases) {
    if (!item.occurred_at) {
      continue;
    }

    const month =
      item.occurred_at.slice(0, 7);

    if (!/^\d{4}-\d{2}$/.test(month)) {
      continue;
    }

    const existing =
      receiptActivityByMonth.get(
        month,
      ) ?? {
        receiptIds: new Set<string>(),
        baseUnits: 0,
      };

    existing.receiptIds.add(
      item.source.id,
    );

    existing.baseUnits +=
      numeric(item.quantity) ?? 0;

    receiptActivityByMonth.set(
      month,
      existing,
    );
  }

  const receiptActivity: ReceiptActivityPoint[] =
    Array.from(
      receiptActivityByMonth.entries(),
    )
      .sort(([left], [right]) =>
        left.localeCompare(right),
      )
      .map(
        ([month, activity]) => ({
          month,
          label: new Intl.DateTimeFormat(
            undefined,
            {
              month: "short",
              year: "numeric",
              timeZone: "UTC",
            },
          ).format(
            new Date(
              `${month}-01T00:00:00Z`,
            ),
          ),
          receiptCount:
            activity.receiptIds.size,
          baseUnits:
            activity.baseUnits,
        }),
      );

  const receiptTimestamps =
    Array.from(
      new Map(
        purchases
          .filter(
            (item) =>
              Boolean(item.occurred_at),
          )
          .map((item) => [
            item.source.id,
            timestamp(item),
          ]),
      ).values(),
    )
      .filter(
        (value) => value > 0,
      )
      .sort(
        (left, right) =>
          left - right,
      );

  const receiptIntervals =
    receiptTimestamps
      .slice(1)
      .map(
        (value, index) =>
          value -
          receiptTimestamps[index],
      )
      .filter(
        (value) => value > 0,
      );

  const averageReceiptCadenceDays =
    receiptIntervals.length > 0
      ? receiptIntervals.reduce(
          (total, interval) =>
            total + interval,
          0,
        ) /
        receiptIntervals.length /
        (24 * 60 * 60 * 1000)
      : null;

  return (
    <div className="mt-4">
      <details className="group overflow-hidden rounded-xl border">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 hover:bg-muted/30 [&::-webkit-details-marker]:hidden">
          <div>
            <p className="font-medium">
              Purchasing history & cost trend
            </p>

            <CardDescription className="mt-1">
              Expand for receipt activity and
              historical recorded base-unit costs
              for {supplierName}.
            </CardDescription>
          </div>

          <ChevronDown className="size-4 shrink-0 transition-transform group-open:rotate-180" />
        </summary>

        <div className="space-y-5 border-t p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border p-4">
              <p className="text-xs text-muted-foreground">
                Receipt documents
              </p>

              <p className="mt-1 text-xl font-semibold">
                {displayNumber(
                  receiptDocumentCount,
                )}
              </p>

              <p className="mt-1 text-xs text-muted-foreground">
                Unique Goods Receipt sources
              </p>
            </div>

            <div className="rounded-xl border p-4">
              <p className="text-xs text-muted-foreground">
                Purchase entries
              </p>

              <p className="mt-1 text-xl font-semibold">
                {displayNumber(
                  purchaseEntryCount,
                )}
              </p>

              <p className="mt-1 text-xs text-muted-foreground">
                Persisted product receipt lines
              </p>
            </div>

            <div className="rounded-xl border p-4">
              <p className="text-xs text-muted-foreground">
                Base units received
              </p>

              <p className="mt-1 text-xl font-semibold">
                {displayNumber(
                  baseUnitsReceived,
                )}
              </p>

              <p className="mt-1 text-xs text-muted-foreground">
                Sum of normalized purchase quantities
              </p>
            </div>
          </div>

          <section className="space-y-3">
            <div>
              <p className="font-medium">
                Documented receipt activity
              </p>

              <p className="mt-1 text-sm text-muted-foreground">
                Posted Goods Receipt activity for this
                supplier in the selected Product
                Intelligence period.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border p-4">
                <p className="text-xs text-muted-foreground">
                  Average days between receipts
                </p>

                <p className="mt-1 text-xl font-semibold">
                  {displayNumber(
                    averageReceiptCadenceDays,
                  )}
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  Calculated only when at least two
                  distinct posted receipts exist.
                </p>
              </div>

              <div className="rounded-xl border p-4">
                <p className="text-xs text-muted-foreground">
                  Active receipt months
                </p>

                <p className="mt-1 text-xl font-semibold">
                  {displayNumber(
                    receiptActivity.length,
                  )}
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  Calendar months with posted receipt
                  evidence.
                </p>
              </div>

              <div className="rounded-xl border p-4">
                <p className="text-xs text-muted-foreground">
                  Total base units received
                </p>

                <p className="mt-1 text-xl font-semibold">
                  {displayNumber(
                    baseUnitsReceived,
                  )}
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  Across the selected supplier period.
                </p>
              </div>
            </div>

            {receiptActivity.length === 0 ? (
              <div className="rounded-xl border border-dashed p-5 text-sm text-muted-foreground">
                No dated posted receipt activity is
                available for this supplier.
              </div>
            ) : (
              <div className="h-64 rounded-xl border p-4">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <BarChart
                    data={receiptActivity}
                    margin={{
                      top: 8,
                      right: 8,
                      left: 0,
                      bottom: 8,
                    }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="label"
                    />

                    <YAxis allowDecimals={false} />

                    <Tooltip
                      content={({ active, payload }) => {
                        if (
                          !active ||
                          !payload?.length
                        ) {
                          return null;
                        }

                        const point =
                          payload[0]
                            .payload as ReceiptActivityPoint;

                        return (
                          <div className="min-w-52 rounded-xl border bg-background p-3 text-sm shadow-lg">
                            <p className="font-medium">
                              {point.label}
                            </p>

                            <p className="mt-2">
                              Posted receipts:{" "}
                              <span className="font-medium">
                                {displayNumber(
                                  point.receiptCount,
                                )}
                              </span>
                            </p>

                            <p className="mt-1">
                              Base units received:{" "}
                              <span className="font-medium">
                                {displayNumber(
                                  point.baseUnits,
                                )}
                              </span>
                            </p>
                          </div>
                        );
                      }}
                    />

                    <Bar
                      dataKey="receiptCount"
                      name="Posted receipts"
                      fill="currentColor"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            <p className="text-xs text-muted-foreground">
              Receipt cadence and activity describe
              documented posted-receipt history only.
              They are not a supplier reliability score
              and do not establish lead times, service
              quality, or future delivery performance.
            </p>
          </section>

          {latestReceipt ? (
            <div className="rounded-xl border p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium">
                    Latest supplier evidence
                  </p>

                  <p className="mt-1 text-sm text-muted-foreground">
                    {displayDate(
                      latestReceipt.occurred_at,
                    )}
                    {" · "}
                    {latestReceipt.source.number}
                  </p>

                  <p className="mt-1 text-sm">
                    Base-unit cost:{" "}
                    <span className="font-medium">
                      {normalizeCurrency(
                        latestReceipt.currency,
                      )
                        ? `${normalizeCurrency(
                            latestReceipt.currency,
                          )} ${displayNumber(
                            latestReceipt.value,
                          )}`
                        : `Currency not recorded · ${displayNumber(
                            latestReceipt.value,
                          )}`}
                    </span>
                  </p>
                </div>

                <Link
                  to={receiptLink(
                    latestReceipt,
                  )}
                  className="inline-flex h-8 items-center justify-center rounded-md border px-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                >
                  Open Goods Receipt
                </Link>
              </div>
            </div>
          ) : null}

          <section className="space-y-3">
            <div>
              <p className="font-medium">
                Recorded cost trend
              </p>

              <p className="mt-1 text-sm text-muted-foreground">
                Each chart keeps receipt currencies
                separate. Points represent persisted
                Goods Receipt cost evidence normalized
                to the product base unit.
              </p>
            </div>

            {costGroups.length === 0 ? (
              <div className="rounded-xl border border-dashed p-5 text-sm text-muted-foreground">
                No chartable supplier cost observations
                are available because a recorded receipt
                currency and numeric cost are required.
              </div>
            ) : (
              <div className="space-y-4">
                {costGroups.map(
                  (group) => (
                    <div
                      key={group.currency}
                      className="rounded-xl border p-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="font-medium">
                            {group.currency} base-unit cost
                          </p>

                          <p className="mt-1 text-xs text-muted-foreground">
                            {group.points.length} recorded
                            cost observation
                            {group.points.length === 1
                              ? ""
                              : "s"}
                          </p>
                        </div>

                        <Badge variant="outline">
                          {group.currency}
                        </Badge>
                      </div>

                      <div className="mt-4 h-64">
                        <ResponsiveContainer
                          width="100%"
                          height="100%"
                        >
                          <LineChart
                            data={group.points}
                            margin={{
                              top: 8,
                              right: 8,
                              left: 0,
                              bottom: 8,
                            }}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                            />

                            <XAxis
                              dataKey="date"
                              tickFormatter={(
                                value,
                              ) =>
                                new Date(
                                  value,
                                ).toLocaleDateString()
                              }
                            />

                            <YAxis />

                            <Tooltip
                              labelFormatter={(
                                value,
                              ) =>
                                displayDate(
                                  String(value),
                                )
                              }
                            />

                            <Line
                              type="monotone"
                              dataKey="cost"
                              name="Base-unit cost"
                              stroke="currentColor"
                              dot
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  ),
                )}
              </div>
            )}

            {costEvidenceWithoutCurrency > 0 ? (
              <p className="text-xs text-muted-foreground">
                {costEvidenceWithoutCurrency} cost
                observation
                {costEvidenceWithoutCurrency === 1
                  ? ""
                  : "s"} had no recorded currency and
                therefore remain visible in the receipt
                history but are excluded from
                currency-specific comparison charts.
              </p>
            ) : null}
          </section>

          <section className="space-y-3">
            <div>
              <p className="font-medium">
                Recent receipt entries
              </p>

              <p className="mt-1 text-sm text-muted-foreground">
                The latest ten persisted purchase
                entries are shown here; the full receipt
                document remains one click away.
              </p>
            </div>

            <div className="overflow-hidden rounded-xl border">
              <div className="divide-y">
                {recentEntries.map(
                  (item) => {
                    const currency =
                      normalizeCurrency(
                        item.currency,
                      );

                    return (
                      <div
                        key={item.id}
                        className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium">
                              {item.source.number}
                            </p>

                            <Badge variant="outline">
                              {item.warehouse.name}
                            </Badge>
                          </div>

                          <p className="mt-1 text-xs text-muted-foreground">
                            {displayDate(
                              item.occurred_at,
                            )}
                          </p>

                          <p className="mt-2 text-sm">
                            Quantity:{" "}
                            <span className="font-medium">
                              {displayNumber(
                                item.quantity,
                              )}
                            </span>
                            {" · "}
                            Base-unit cost:{" "}
                            <span className="font-medium">
                              {currency
                                ? `${currency} ${displayNumber(
                                    item.value,
                                  )}`
                                : `Currency not recorded · ${displayNumber(
                                    item.value,
                                  )}`}
                            </span>
                          </p>
                        </div>

                        <Link
                          to={receiptLink(item)}
                          className="inline-flex h-8 shrink-0 items-center justify-center rounded-md border px-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                        >
                          Open Receipt
                        </Link>
                      </div>
                    );
                  },
                )}
              </div>
            </div>
          </section>

          <p className="text-xs text-muted-foreground">
            This drill-down reports persisted posted
            Goods Receipt evidence only. It does not
            infer supplier reliability, future pricing,
            lead times, payment terms, delivery costs,
            or commercial preference.
          </p>
        </div>
      </details>
    </div>
  );
}

export default ProductSupplierHistoryPanel;
