import {
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

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

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
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
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          These metrics describe persisted
          activity in the currently selected
          Product Intelligence period. Gross
          sales are not netted against refunds.
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
