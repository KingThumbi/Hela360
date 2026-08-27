import {
  ArrowLeft,
  PackagePlus,
} from "lucide-react";
import type { ReactNode } from "react";
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
  useGoodsReceipt,
} from "@/hooks/queries/inventory";
import { PATHS } from "@/routes/routes";
import type {
  GoodsReceipt,
} from "@/types/entities";

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

function money(value: string): string {
  const normalized = Number(value);
  return Number.isFinite(normalized)
    ? normalized.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    : value;
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

export function GoodsReceiptDetailPage() {
  const {
    receiptId,
  } = useParams();
  const receiptQuery = useGoodsReceipt(receiptId);

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Goods Receipt</PageTitle>
          <PageDescription>
            Persisted stock receiving confirmation.
          </PageDescription>
        </div>

        <PageActions>
          <Link
            to={PATHS.INVENTORY.ROOT}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Inventory
          </Link>
          <Link
            to={PATHS.INVENTORY.RECEIPTS}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            Receiving History
          </Link>
          <Link
            to={PATHS.INVENTORY.RECEIVE}
            className={buttonVariants()}
          >
            <PackagePlus />
            Receive Another
          </Link>
        </PageActions>
      </PageHeader>

      <PageContent>
        {!receiptId ? (
          <PageSection>
            <EmptyState
              title="Receipt not selected"
              description="Open a persisted goods receipt to view confirmation details."
            />
          </PageSection>
        ) : receiptQuery.isLoading ? (
          <PageSection>
            <LoadingState title="Loading goods receipt" />
          </PageSection>
        ) : receiptQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Goods receipt unavailable"
              description={errorMessage(receiptQuery.error)}
            />
          </PageSection>
        ) : receiptQuery.data ? (
          <GoodsReceiptDetail receipt={receiptQuery.data} />
        ) : null}
      </PageContent>
    </Page>
  );
}

function GoodsReceiptDetail({
  receipt,
}: {
  receipt: GoodsReceipt;
}) {
  return (
    <>
      <PageSection>
        <div className="grid gap-4 lg:grid-cols-4">
          <DetailBlock
            label="Receipt"
            value={receipt.receipt_number}
          />
          <DetailBlock
            label="Warehouse"
            value={`${receipt.warehouse.code} - ${receipt.warehouse.name}`}
          />
          <DetailBlock
            label="Supplier"
            value={
              receipt.supplier
                ? `${receipt.supplier.supplier_code} - ${receipt.supplier.name}`
                : "No supplier"
            }
          />
          <DetailBlock
            label="Status"
            value={<Badge variant="outline">{receipt.status}</Badge>}
          />
          <DetailBlock
            label="Supplier Reference"
            value={receipt.supplier_reference ?? "None"}
          />
          <DetailBlock
            label="Received"
            value={dateTimeLabel(receipt.received_at)}
          />
          <DetailBlock
            label="Received By"
            value={
              receipt.received_by?.name ??
              receipt.received_by?.username ??
              "Unknown"
            }
          />
          <DetailBlock
            label="Notes"
            value={receipt.notes ?? "None"}
          />
        </div>
      </PageSection>

      <PageSection>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Line</TableHead>
              <TableHead>Product</TableHead>
              <TableHead>Quantity</TableHead>
              <TableHead>Batch</TableHead>
              <TableHead>Manufacture</TableHead>
              <TableHead>Expiry</TableHead>
              <TableHead>Unit Cost</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {receipt.items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.line_number}</TableCell>
                <TableCell className="whitespace-normal">
                  <div className="font-medium">
                    {item.product.name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {item.product.internal_sku}
                  </div>
                </TableCell>
                <TableCell>{quantity(item.quantity)}</TableCell>
                <TableCell>
                  {item.batch?.batch_number ?? item.batch_number ?? "None"}
                </TableCell>
                <TableCell>{dateLabel(item.manufacture_date)}</TableCell>
                <TableCell>{dateLabel(item.expiry_date)}</TableCell>
                <TableCell>{money(item.unit_cost)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </PageSection>
    </>
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
      <div className="text-xs uppercase text-muted-foreground">
        {label}
      </div>
      <div className="text-sm font-medium">
        {value}
      </div>
    </div>
  );
}

export default GoodsReceiptDetailPage;
