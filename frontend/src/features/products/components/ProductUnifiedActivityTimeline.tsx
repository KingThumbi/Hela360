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
  ProductStockCountHistoryItem,
} from "@/types/responses/product-history";

type ActivitySourceLink = {
  label: string;
  path: string;
};

type ProductActivityEvent = {
  id: string;
  occurredAt: string | null;

  kind:
    | "sale"
    | "purchase"
    | "refund"
    | "stock_count"
    | "adjustment"
    | "movement";

  title: string;
  status?: string | null;

  warehouse?: string | null;
  quantity?: string | null;

  detailLines: string[];

  sourceLinks: ActivitySourceLink[];
};

function displayNumber(
  value: string | number | null | undefined,
) {
  if (value == null || value === "") {
    return "—";
  }

  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return String(value);
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

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

function lifecycleLabel(value: string) {
  switch (value) {
    case "counting":
      return "Counting";
    case "awaiting_posting":
      return "Awaiting posting";
    case "posted":
      return "Posted";
    case "completed":
      return "Completed";
    case "cancelled":
      return "Cancelled";
    case "superseded":
      return "Superseded";
    default:
      return value;
  }
}

function kindLabel(
  kind: ProductActivityEvent["kind"],
) {
  switch (kind) {
    case "sale":
      return "Sale";
    case "purchase":
      return "Purchase";
    case "refund":
      return "Refund";
    case "stock_count":
      return "Stock Count";
    case "adjustment":
      return "Adjustment";
    default:
      return "Inventory movement";
  }
}

function movementSourceLink(
  item: ProductMovementHistoryItem,
): ActivitySourceLink | null {
  const referenceType =
    item.reference?.type;

  const referenceId =
    item.reference?.id;

  if (!referenceId) {
    return null;
  }

  if (referenceType === "sale") {
    return {
      label: "Open Sale Receipt",
      path: PATHS.SALES.receipt(
        referenceId,
      ),
    };
  }

  if (referenceType === "goods_receipt") {
    return {
      label: "Open Goods Receipt",
      path: PATHS.INVENTORY.receipt(
        referenceId,
      ),
    };
  }

  if (referenceType === "stock_adjustment") {
    return {
      label: "Open Stock Adjustment",
      path: PATHS.INVENTORY.stockAdjustment(
        referenceId,
      ),
    };
  }

  return null;
}

function buildActivityEvents({
  sales,
  purchases,
  movements,
  stockCounts,
}: {
  sales: ProductPriceTrendItem[];
  purchases: ProductPriceTrendItem[];
  movements: ProductMovementHistoryItem[];
  stockCounts: ProductStockCountHistoryItem[];
}) {
  const events: ProductActivityEvent[] = [];

  const stockCountIds = new Set(
    stockCounts.map(
      (item) => item.stock_count.id,
    ),
  );

  const stockCountAdjustmentIds = new Set(
    stockCounts
      .map(
        (item) => item.adjustment?.id,
      )
      .filter(
        (value): value is string =>
          Boolean(value),
      ),
  );

  for (const item of sales) {
    const detailLines = [
      `Base quantity: ${displayNumber(
        item.quantity,
      )}`,
      `Normalized selling price: ${displayNumber(
        item.value,
      )}`,
    ];

    if (item.transaction_value) {
      detailLines.push(
        `Transaction unit price: ${displayNumber(
          item.transaction_value,
        )}`,
      );
    }

    if (item.refund_status) {
      detailLines.push(
        `Refund status: ${item.refund_status}`,
      );
    }

    if (item.is_returned) {
      detailLines.push(
        "Sale line has return evidence",
      );
    }

    events.push({
      id: `sale:${item.id}`,
      occurredAt: item.occurred_at,
      kind: "sale",
      title: item.source.number,
      status: item.status,
      warehouse: item.warehouse.name,
      quantity: item.quantity,
      detailLines,
      sourceLinks: [
        {
          label: "Open Sale Receipt",
          path: PATHS.SALES.receipt(
            item.source.id,
          ),
        },
      ],
    });
  }

  for (const item of purchases) {
    const detailLines = [
      `Base quantity: ${displayNumber(
        item.quantity,
      )}`,
      `Base-unit cost: ${displayNumber(
        item.value,
      )}`,
    ];

    if (item.transaction_value) {
      detailLines.push(
        `Transaction unit cost: ${displayNumber(
          item.transaction_value,
        )}`,
      );
    }

    if (item.supplier?.name) {
      detailLines.push(
        `Supplier: ${item.supplier.name}`,
      );
    }

    events.push({
      id: `purchase:${item.id}`,
      occurredAt: item.occurred_at,
      kind: "purchase",
      title: item.source.number,
      warehouse: item.warehouse.name,
      quantity: item.quantity,
      detailLines,
      sourceLinks: [
        {
          label: "Open Goods Receipt",
          path: PATHS.INVENTORY.receipt(
            item.source.id,
          ),
        },
      ],
    });
  }

  for (const item of stockCounts) {
    const detailLines: string[] = [];

    if (
      item.line.expected_quantity !==
      undefined
    ) {
      detailLines.push(
        `Expected quantity: ${displayNumber(
          item.line.expected_quantity,
        )}`,
      );
    } else {
      detailLines.push(
        "System quantity hidden during blind counting",
      );
    }

    detailLines.push(
      `Counted quantity: ${displayNumber(
        item.line.counted_quantity,
      )}`,
    );

    if (
      item.line.variance_quantity !==
      undefined
    ) {
      detailLines.push(
        `Variance: ${displayNumber(
          item.line.variance_quantity,
        )}`,
      );
    }

    if (
      item.line.counted_unit_quantity !=
      null
    ) {
      const unit =
        item.line.counted_unit_code ??
        item.line.counted_unit_name ??
        "";

      let physicalEntry =
        `Physical entry: ${displayNumber(
          item.line.counted_unit_quantity,
        )} ${unit}`.trim();

      if (
        item.line
          .counted_conversion_factor_to_base !=
        null
      ) {
        physicalEntry +=
          ` × ${displayNumber(
            item.line
              .counted_conversion_factor_to_base,
          )}` +
          ` → ${displayNumber(
            item.line.counted_quantity,
          )} base units`;
      }

      detailLines.push(
        physicalEntry,
      );
    }

    const batchNumber =
      item.line.batch?.batch_number ??
      item.line.observed_batch_number;

    if (batchNumber) {
      detailLines.push(
        `Batch: ${batchNumber}`,
      );
    }

    if (item.adjustment) {
      detailLines.push(
        `Adjustment ${item.adjustment.adjustment_number}: ` +
          `${displayNumber(
            item.adjustment.quantity_delta,
          )}`,
      );
    }

    const sourceLinks: ActivitySourceLink[] = [
      {
        label: "Open Stock Count",
        path: PATHS.INVENTORY.stockCount(
          item.stock_count.id,
        ),
      },
    ];

    if (item.adjustment?.id) {
      sourceLinks.push({
        label: "Open Stock Adjustment",
        path:
          PATHS.INVENTORY.stockAdjustment(
            item.adjustment.id,
          ),
      });
    }

    events.push({
      id: `stock-count:${item.line.id}`,
      occurredAt:
        item.adjustment?.posted_at ??
        item.stock_count.completed_at ??
        item.stock_count.started_at,
      kind: "stock_count",
      title:
        item.stock_count.count_number,
      status: lifecycleLabel(
        item.stock_count.lifecycle,
      ),
      warehouse: item.warehouse.name,
      quantity:
        item.line.counted_quantity,
      detailLines,
      sourceLinks,
    });
  }

  for (const item of movements) {
    const referenceType =
      item.reference?.type;

    const referenceId =
      item.reference?.id;

    /*
     * Do not duplicate document-backed events already represented
     * above by their richer Sale / Goods Receipt evidence.
     */
    if (
      referenceType === "sale" ||
      referenceType === "goods_receipt"
    ) {
      continue;
    }

    /*
     * A posted Stock Count already carries its resulting adjustment.
     * Suppress only that linked adjustment movement. Standalone/manual
     * Stock Adjustments remain visible.
     */
    if (
      referenceType === "stock_adjustment" &&
      referenceId &&
      stockCountAdjustmentIds.has(
        referenceId,
      )
    ) {
      continue;
    }

    if (
      referenceType === "stock_count" &&
      referenceId &&
      stockCountIds.has(referenceId)
    ) {
      continue;
    }

    const isRefund =
      referenceType === "sale_refund" ||
      item.movement_type ===
        "sale_refund";

    const isAdjustment =
      referenceType ===
        "stock_adjustment" ||
      item.movement_type ===
        "stock_adjustment";

    const sourceLink =
      movementSourceLink(item);

    const detailLines = [
      `Signed quantity: ${displayNumber(
        item.quantity,
      )}`,
    ];

    if (item.batch?.batch_number) {
      detailLines.push(
        `Batch: ${item.batch.batch_number}`,
      );
    }

    if (item.unit_cost != null) {
      detailLines.push(
        `Persisted unit cost: ${displayNumber(
          item.unit_cost,
        )}`,
      );
    }

    if (item.unit_price != null) {
      detailLines.push(
        `Persisted unit price: ${displayNumber(
          item.unit_price,
        )}`,
      );
    }

    const actor =
      item.performed_by?.name ??
      item.performed_by?.username;

    if (actor) {
      detailLines.push(
        `Performed by: ${actor}`,
      );
    }

    if (referenceType) {
      detailLines.push(
        `Ledger reference: ${referenceType}`,
      );
    }

    events.push({
      id: `movement:${item.id}`,
      occurredAt: item.created_at,
      kind: isRefund
        ? "refund"
        : isAdjustment
          ? "adjustment"
          : "movement",
      title: item.movement_type,
      warehouse:
        item.warehouse?.name ?? null,
      quantity: item.quantity,
      detailLines,
      sourceLinks: sourceLink
        ? [sourceLink]
        : [],
    });
  }

  events.sort((left, right) => {
    const leftTime = left.occurredAt
      ? new Date(
          left.occurredAt,
        ).getTime()
      : 0;

    const rightTime = right.occurredAt
      ? new Date(
          right.occurredAt,
        ).getTime()
      : 0;

    if (leftTime !== rightTime) {
      return rightTime - leftTime;
    }

    return left.id.localeCompare(
      right.id,
    );
  });

  return events;
}

export function ProductUnifiedActivityTimeline({
  sales,
  purchases,
  movements,
  stockCounts,
  isLoading,
  sourceErrors,
}: {
  sales: ProductPriceTrendItem[];
  purchases: ProductPriceTrendItem[];
  movements: ProductMovementHistoryItem[];
  stockCounts: ProductStockCountHistoryItem[];
  isLoading: boolean;
  sourceErrors: string[];
}) {
  const events = buildActivityEvents({
    sales,
    purchases,
    movements,
    stockCounts,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Unified product activity
        </CardTitle>

        <CardDescription>
          One chronological evidence trail across
          sales, receipts, refunds, physical counts,
          stock adjustments, and other inventory
          movements.
        </CardDescription>
      </CardHeader>

      <CardContent>
        {sourceErrors.length > 0 ? (
          <div className="mb-4 rounded-xl border border-destructive/30 p-4">
            <p className="font-medium">
              Partial activity evidence
            </p>

            <p className="mt-1 text-sm text-muted-foreground">
              One or more authorized evidence
              sources could not be loaded:
              {" "}
              {sourceErrors.join(", ")}.
            </p>
          </div>
        ) : null}

        {isLoading && events.length === 0 ? (
          <div className="rounded-xl border border-dashed p-8 text-center">
            <p className="font-medium">
              Loading product activity
            </p>

            <p className="mt-1 text-sm text-muted-foreground">
              Loading complete authorized evidence
              for the selected period.
            </p>
          </div>
        ) : events.length === 0 ? (
          <div className="rounded-xl border border-dashed p-8 text-center">
            <p className="font-medium">
              No product activity
            </p>

            <p className="mt-1 text-sm text-muted-foreground">
              No authorized persisted evidence was
              found for the selected period.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div
                key={event.id}
                className="rounded-xl border p-4"
              >
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline">
                        {kindLabel(
                          event.kind,
                        )}
                      </Badge>

                      <span className="font-medium">
                        {event.title}
                      </span>

                      {event.status ? (
                        <Badge variant="secondary">
                          {event.status}
                        </Badge>
                      ) : null}
                    </div>

                    <p className="text-sm text-muted-foreground">
                      {displayDate(
                        event.occurredAt,
                      )}

                      {event.warehouse
                        ? ` · ${event.warehouse}`
                        : ""}
                    </p>

                    <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
                      {event.detailLines.map(
                        (line) => (
                          <span
                            key={`${event.id}:${line}`}
                          >
                            {line}
                          </span>
                        ),
                      )}
                    </div>
                  </div>

                  {event.sourceLinks.length >
                  0 ? (
                    <div className="flex flex-wrap gap-2">
                      {event.sourceLinks.map(
                        (link) => (
                          <Link
                            key={`${event.id}:${link.path}`}
                            to={link.path}
                            className="inline-flex h-9 items-center justify-center rounded-md border px-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                          >
                            {link.label}
                          </Link>
                        ),
                      )}
                    </div>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        )}

        <p className="mt-4 text-xs text-muted-foreground">
          Document-backed Sale and Goods Receipt
          ledger movements are deduplicated here.
          Refunds and standalone inventory movements
          remain separate evidence. This timeline
          does not reconstruct historical stock
          balances or calculate profitability.
        </p>
      </CardContent>
    </Card>
  );
}

export default ProductUnifiedActivityTimeline;
