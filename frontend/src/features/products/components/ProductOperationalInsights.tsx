import {
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import type { Product } from "@/types/entities";
import type {
  ProductPriceTrendItem,
  ProductStockCountHistoryItem,
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
    maximumFractionDigits: 4,
  }).format(parsed);
}


function displayDate(
  value: string | null | undefined,
) {
  if (!value) {
    return "—";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}


function latestDate(
  values: Array<
    string | null | undefined
  >,
) {
  const candidates = values
    .filter(
      (value): value is string =>
        Boolean(value),
    )
    .map((value) => ({
      value,
      timestamp:
        new Date(value).getTime(),
    }))
    .filter((item) =>
      Number.isFinite(
        item.timestamp,
      ),
    )
    .sort(
      (left, right) =>
        right.timestamp -
        left.timestamp,
    );

  return candidates[0]?.value ?? null;
}


export function ProductOperationalInsights({
  product,
  quantityAvailable,
  sales,
  purchases,
  stockCounts,
}: {
  product: Product;
  quantityAvailable:
    | string
    | null
    | undefined;
  sales: ProductPriceTrendItem[];
  purchases: ProductPriceTrendItem[];
  stockCounts: ProductStockCountHistoryItem[];
}) {
  const grossBaseUnitsSold =
    sales.reduce(
      (total, item) =>
        total +
        (numeric(item.quantity) ?? 0),
      0,
    );

  const saleLineCount =
    sales.length;

  const sellingDays =
    new Set(
      sales
        .map(
          (item) =>
            item.occurred_at
              ?.slice(0, 10) ??
            null,
        )
        .filter(
          (value): value is string =>
            Boolean(value),
        ),
    ).size;

  const averagePerSellingDay =
    sellingDays > 0
      ? grossBaseUnitsSold /
        sellingDays
      : null;

  const returnedSaleLines =
    sales.filter(
      (item) =>
        Boolean(
          item.is_returned,
        ),
    ).length;

  const lastSaleAt =
    latestDate(
      sales.map(
        (item) =>
          item.occurred_at,
      ),
    );

  const lastReceiptAt =
    latestDate(
      purchases.map(
        (item) =>
          item.occurred_at,
      ),
    );

  const lastCountAt =
    latestDate(
      stockCounts.map(
        (item) =>
          item.stock_count
            .completed_at ??
          item.stock_count
            .started_at,
      ),
    );

  const available =
    numeric(
      quantityAvailable,
    );

  const reorderLevel =
    numeric(
      product.reorder_level,
    );

  const reorderQty =
    numeric(
      product.reorder_qty,
    );

  const reorderConfigured =
    reorderLevel != null &&
    reorderLevel > 0;

  const reorderAttention =
    reorderConfigured &&
    available != null &&
    available <= reorderLevel;

  const [nowMs] = useState(
    () => Date.now(),
  );

  const trailing30StartMs =
    nowMs -
    30 * 24 * 60 * 60 * 1000;

  const trailing30Sales =
    sales.filter((item) => {
      if (!item.occurred_at) {
        return false;
      }

      const timestamp =
        new Date(
          item.occurred_at,
        ).getTime();

      return (
        Number.isFinite(timestamp) &&
        timestamp >= trailing30StartMs &&
        timestamp <= nowMs
      );
    });

  const trailing30GrossUnits =
    trailing30Sales.reduce(
      (total, item) =>
        total +
        (numeric(item.quantity) ?? 0),
      0,
    );

  /*
   * Calendar-day pace is deliberate.
   * This is more suitable for stock-cover context
   * than averaging only across days when a sale occurred.
   */
  const trailing30DailyPace =
    trailing30GrossUnits > 0
      ? trailing30GrossUnits / 30
      : null;

  const estimatedCoverageDays =
    (
      available != null &&
      available >= 0 &&
      trailing30DailyPace != null &&
      trailing30DailyPace > 0
    )
      ? available /
        trailing30DailyPace
      : null;

  const reorderGap =
    (
      reorderConfigured &&
      available != null
    )
      ? Math.max(
          reorderLevel - available,
          0,
        )
      : null;

  const projectedAvailableAfterReorder =
    (
      available != null &&
      reorderQty != null &&
      reorderQty > 0
    )
      ? available + reorderQty
      : null;

  const projectedCoverageAfterReorder =
    (
      projectedAvailableAfterReorder != null &&
      trailing30DailyPace != null &&
      trailing30DailyPace > 0
    )
      ? projectedAvailableAfterReorder /
        trailing30DailyPace
      : null;

  const coverageSignal =
    estimatedCoverageDays == null
      ? "unavailable"
      : estimatedCoverageDays <= 7
        ? "short"
        : estimatedCoverageDays <= 14
          ? "watch"
          : "comfortable";

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>
              Operational insights
            </CardTitle>

            <CardDescription>
              Evidence-backed sales activity,
              recency, and configured reorder
              context for this product.
            </CardDescription>
          </div>

          {reorderConfigured ? (
            reorderAttention ? (
              <Badge
                variant="outline"
                className="gap-1.5 border-amber-500/40"
              >
                <AlertTriangle className="size-3.5" />
                Reorder attention
              </Badge>
            ) : (
              <Badge
                variant="outline"
                className="gap-1.5"
              >
                <CheckCircle2 className="size-3.5" />
                Above reorder level
              </Badge>
            )
          ) : (
            <Badge variant="outline">
              Reorder threshold not configured
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-xl border p-4">
            <p className="text-xs text-muted-foreground">
              Gross base units sold
            </p>

            <p className="mt-1 text-xl font-semibold">
              {displayNumber(
                grossBaseUnitsSold,
              )}
            </p>

            <p className="mt-1 text-xs text-muted-foreground">
              Before refunds/returns
            </p>
          </div>

          <div className="rounded-xl border p-4">
            <p className="text-xs text-muted-foreground">
              Sale lines
            </p>

            <p className="mt-1 text-xl font-semibold">
              {displayNumber(
                saleLineCount,
              )}
            </p>

            <p className="mt-1 text-xs text-muted-foreground">
              {returnedSaleLines} with
              return evidence
            </p>
          </div>

          <div className="rounded-xl border p-4">
            <p className="text-xs text-muted-foreground">
              Selling days
            </p>

            <p className="mt-1 text-xl font-semibold">
              {displayNumber(
                sellingDays,
              )}
            </p>

            <p className="mt-1 text-xs text-muted-foreground">
              Days with persisted sale
              evidence
            </p>
          </div>

          <div className="rounded-xl border p-4">
            <p className="text-xs text-muted-foreground">
              Avg. units / selling day
            </p>

            <p className="mt-1 text-xl font-semibold">
              {displayNumber(
                averagePerSellingDay,
              )}
            </p>

            <p className="mt-1 text-xs text-muted-foreground">
              Gross base-unit activity
            </p>
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-3">
          <div className="rounded-xl border p-4">
            <p className="text-xs text-muted-foreground">
              Latest sale evidence
            </p>

            <p className="mt-1 font-medium">
              {displayDate(
                lastSaleAt,
              )}
            </p>
          </div>

          <div className="rounded-xl border p-4">
            <p className="text-xs text-muted-foreground">
              Latest posted receipt
            </p>

            <p className="mt-1 font-medium">
              {displayDate(
                lastReceiptAt,
              )}
            </p>
          </div>

          <div className="rounded-xl border p-4">
            <p className="text-xs text-muted-foreground">
              Latest physical count
            </p>

            <p className="mt-1 font-medium">
              {displayDate(
                lastCountAt,
              )}
            </p>
          </div>
        </div>

        <div className="rounded-xl border p-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-medium">
                Stock coverage heuristic
              </p>

              <p className="mt-1 text-sm text-muted-foreground">
                Current available stock compared with
                gross base-unit sales over the trailing
                30 calendar days.
              </p>
            </div>

            {coverageSignal === "short" ? (
              <Badge
                variant="outline"
                className="border-amber-500/40"
              >
                Short cover
              </Badge>
            ) : coverageSignal === "watch" ? (
              <Badge variant="outline">
                Watch coverage
              </Badge>
            ) : coverageSignal === "comfortable" ? (
              <Badge variant="secondary">
                More than 14 days cover
              </Badge>
            ) : (
              <Badge variant="outline">
                Coverage unavailable
              </Badge>
            )}
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">
                Gross units · last 30 days
              </p>

              <p className="mt-1 font-medium">
                {displayNumber(
                  trailing30GrossUnits,
                )}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">
                Gross units / calendar day
              </p>

              <p className="mt-1 font-medium">
                {displayNumber(
                  trailing30DailyPace,
                )}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">
                Estimated days of cover
              </p>

              <p className="mt-1 font-medium">
                {displayNumber(
                  estimatedCoverageDays,
                )}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">
                Cover after configured reorder qty
              </p>

              <p className="mt-1 font-medium">
                {displayNumber(
                  projectedCoverageAfterReorder,
                )}
              </p>
            </div>
          </div>

          {trailing30DailyPace == null ? (
            <p className="mt-3 text-xs text-muted-foreground">
              No positive gross sales activity was found
              in the trailing 30 days, so Hela360 does
              not estimate days of cover for this product.
            </p>
          ) : (
            <p className="mt-3 text-xs text-muted-foreground">
              Coverage = current available stock ÷ trailing
              30-day gross base-unit sales pace. This is an
              operational heuristic, not a demand forecast
              or replenishment recommendation.
            </p>
          )}
        </div>

        <div className="rounded-xl border p-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-medium">
                Reorder context
              </p>

              <p className="mt-1 text-sm text-muted-foreground">
                Uses the product's configured
                reorder level and current
                available stock only.
              </p>
            </div>

            {reorderAttention ? (
              <Badge
                variant="outline"
                className="border-amber-500/40"
              >
                Review replenishment
              </Badge>
            ) : null}
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">
                Available now
              </p>

              <p className="mt-1 font-medium">
                {displayNumber(
                  available,
                )}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">
                Reorder level
              </p>

              <p className="mt-1 font-medium">
                {displayNumber(
                  product.reorder_level,
                )}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">
                Configured reorder qty
              </p>

              <p className="mt-1 font-medium">
                {displayNumber(
                  reorderQty,
                )}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">
                Units below reorder level
              </p>

              <p className="mt-1 font-medium">
                {displayNumber(
                  reorderGap,
                )}
              </p>
            </div>
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          Period metrics describe persisted
          evidence in the currently selected
          Product Intelligence period. The
          coverage heuristic separately uses
          only sale evidence dated within the
          trailing 30 calendar days. Gross sales
          are not netted against refunds.
          Stock-out frequency is intentionally
          not inferred because Hela360 does not
          yet maintain validated historical
          stock-balance snapshots for that
          purpose.
        </p>
      </CardContent>
    </Card>
  );
}

export default ProductOperationalInsights;
