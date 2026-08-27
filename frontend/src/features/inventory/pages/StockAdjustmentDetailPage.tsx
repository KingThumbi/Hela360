import {
  ArrowLeft,
  ClipboardList,
  RefreshCw,
} from "lucide-react";
import type {
  ReactNode,
} from "react";
import {
  Link,
  useParams,
} from "react-router-dom";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  Page,
  PageActions,
  PageContent,
  PageDescription,
  PageHeader,
  PageSection,
  PageTitle,
} from "@/components/page";
import { Badge } from "@/components/ui/badge";
import {
  Button,
  buttonVariants,
} from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useStockAdjustment,
} from "@/hooks/queries/inventory";
import {
  useAuthorization,
} from "@/hooks/useAuthorization";
import { PATHS } from "@/routes/routes";
import type {
  StockAdjustment,
  StockAdjustmentItem,
} from "@/types/entities";
import type {
  StockAdjustmentReasonCode,
} from "@/types/requests";

const REASON_LABELS: Record<StockAdjustmentReasonCode, string> = {
  stock_count: "Stock Count",
  damage: "Damage",
  expiry: "Expiry",
  breakage: "Breakage",
  correction: "Correction",
  opening_balance: "Opening Balance",
  other: "Other",
};

function dateTimeLabel(value: string | null): string {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleString();
}

function dateLabel(value: string | null): string {
  if (!value) {
    return "None";
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function quantity(value: string): string {
  const normalized = Number(value);
  return Number.isFinite(normalized)
    ? normalized.toLocaleString(undefined, {
        maximumFractionDigits: 4,
      })
    : value;
}

function signedQuantity(value: string): string {
  const normalized = Number(value);
  if (!Number.isFinite(normalized)) {
    return value;
  }

  return `${normalized > 0 ? "+" : ""}${quantity(value)}`;
}

function directionLabel(value: string): "Increase" | "Decrease" {
  return Number(value) < 0 ? "Decrease" : "Increase";
}

function sourceLabel(adjustment: StockAdjustment): string {
  if (adjustment.source.type === "stock_count") {
    return adjustment.source.stock_count
      ? `Stock Count ${adjustment.source.stock_count.count_number}`
      : "Stock Count";
  }

  return "Manual";
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

export function StockAdjustmentDetailPage() {
  const {
    adjustmentId,
  } = useParams();
  const adjustmentQuery = useStockAdjustment(adjustmentId);
  const authorization = useAuthorization();
  const adjustment = adjustmentQuery.data;
  const canViewSourceCount =
    authorization.can("inventory.count") &&
    adjustment?.source.type === "stock_count" &&
    Boolean(adjustment.source.stock_count?.id);

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Stock Adjustment</PageTitle>
          <PageDescription>
            Posted quantity correction and immutable movement audit source.
          </PageDescription>
        </div>

        <PageActions>
          <Link
            to={PATHS.INVENTORY.STOCK_ADJUSTMENTS}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Stock Adjustments
          </Link>
          {canViewSourceCount && adjustment?.source.stock_count ? (
            <Link
              to={PATHS.INVENTORY.stockCount(adjustment.source.stock_count.id)}
              className={buttonVariants({
                variant: "outline",
              })}
            >
              <ClipboardList />
              View Stock Count
            </Link>
          ) : null}
          <Button
            type="button"
            variant="outline"
            onClick={() => adjustmentQuery.refetch()}
            disabled={adjustmentQuery.isFetching}
          >
            <RefreshCw
              className={adjustmentQuery.isFetching ? "animate-spin" : undefined}
            />
            Refresh
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        {!adjustmentId ? (
          <PageSection>
            <EmptyState
              title="Adjustment not selected"
              description="Open a Stock Adjustment to review the posted correction."
            />
          </PageSection>
        ) : adjustmentQuery.isLoading ? (
          <PageSection>
            <LoadingState title="Loading Stock Adjustment" />
          </PageSection>
        ) : adjustmentQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Stock Adjustment unavailable"
              description={errorMessage(adjustmentQuery.error)}
            />
          </PageSection>
        ) : adjustment ? (
          <>
            <PageSection>
              <div className="grid gap-4 lg:grid-cols-4">
                <DetailBlock
                  label="Adjustment #"
                  value={adjustment.adjustment_number}
                />
                <DetailBlock
                  label="Status"
                  value={<Badge variant="secondary">{adjustment.status}</Badge>}
                />
                <DetailBlock
                  label="Warehouse"
                  value={`${adjustment.warehouse.code} - ${adjustment.warehouse.name}`}
                />
                <DetailBlock
                  label="Source"
                  value={sourceLabel(adjustment)}
                />
                <DetailBlock
                  label="Reason"
                  value={REASON_LABELS[adjustment.reason_code]}
                />
                <DetailBlock
                  label="Posted"
                  value={dateTimeLabel(adjustment.posted_at)}
                />
                <DetailBlock
                  label="Posted By"
                  value={
                    adjustment.posted_by?.name ??
                    adjustment.posted_by?.username ??
                    "Unknown"
                  }
                />
                <DetailBlock
                  label="Created"
                  value={dateTimeLabel(adjustment.created_at)}
                />
              </div>
            </PageSection>

            <PageSection>
              <div className="rounded-md border bg-muted/20 p-4 text-sm text-muted-foreground">
                Posted Stock Adjustments are read-only. Corrections to an incorrect adjustment require a later compensating adjustment.
              </div>
            </PageSection>

            {(adjustment.reason || adjustment.notes) ? (
              <PageSection>
                <div className="grid gap-4 md:grid-cols-2">
                  <DetailBlock
                    label="Reason Notes"
                    value={adjustment.reason ?? "None"}
                  />
                  <DetailBlock
                    label="Notes"
                    value={adjustment.notes ?? "None"}
                  />
                </div>
              </PageSection>
            ) : null}

            <PageSection>
              <AdjustmentItemsTable items={adjustment.items} />
            </PageSection>
          </>
        ) : null}
      </PageContent>
    </Page>
  );
}

function AdjustmentItemsTable({
  items,
}: {
  items: StockAdjustmentItem[];
}) {
  return (
    <div className="overflow-x-auto rounded-md border">
      <Table className="min-w-[980px]">
        <TableHeader>
          <TableRow>
            <TableHead>Line</TableHead>
            <TableHead>Product</TableHead>
            <TableHead>Batch</TableHead>
            <TableHead>Expiry</TableHead>
            <TableHead>Effect</TableHead>
            <TableHead className="text-right">Quantity Delta</TableHead>
            <TableHead>Reason</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell>{item.line_number}</TableCell>
              <TableCell>
                <div className="font-medium">{item.product.name}</div>
                <div className="text-xs text-muted-foreground">
                  {item.product.internal_sku}
                </div>
              </TableCell>
              <TableCell>{item.batch?.batch_number ?? "None"}</TableCell>
              <TableCell>{dateLabel(item.batch?.expiry_date ?? null)}</TableCell>
              <TableCell>
                <Badge variant={Number(item.quantity_delta) < 0 ? "secondary" : "outline"}>
                  {directionLabel(item.quantity_delta)}
                </Badge>
              </TableCell>
              <TableCell className="text-right font-medium">
                {signedQuantity(item.quantity_delta)}
              </TableCell>
              <TableCell>{item.reason ?? "None"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function DetailBlock({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="space-y-1 rounded-md border p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-sm font-medium">{value}</div>
    </div>
  );
}

export default StockAdjustmentDetailPage;
