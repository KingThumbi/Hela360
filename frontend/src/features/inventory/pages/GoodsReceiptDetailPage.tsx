import {
  ArrowLeft,
  CheckCircle2,
  ClipboardCheck,
  PackageCheck,
  PackagePlus,
  XCircle,
} from "lucide-react";
import {
  useState,
  type ReactNode,
} from "react";
import {
  Link,
  useParams,
} from "react-router-dom";
import { toast } from "sonner";

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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
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
  useApproveGoodsReceipt,
  useCancelGoodsReceipt,
  useGoodsReceipt,
  usePostGoodsReceipt,
  useReviewGoodsReceipt,
} from "@/hooks/queries/inventory";
import { useAuthorization } from "@/hooks/useAuthorization";
import { PATHS } from "@/routes/routes";
import type {
  GoodsReceipt,
  GoodsReceiptStatus,
} from "@/types/entities";

function dateTimeLabel(value: string | null | undefined): string {
  if (!value) {
    return "Not recorded";
  }

  return new Date(value).toLocaleString();
}

function dateLabel(value: string | null | undefined): string {
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

function money(value: string | null | undefined): string {
  if (value === null || value === undefined) {
    return "None";
  }

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

function statusLabel(status: GoodsReceiptStatus): string {
  switch (status) {
    case "draft":
      return "Draft";
    case "receiving":
      return "Receiving";
    case "received":
      return "Received";
    case "under_review":
      return "Under Review";
    case "approved":
      return "Approved";
    case "posted":
      return "Posted";
    case "cancelled":
      return "Cancelled";
  }
}

function lifecycleDescription(status: GoodsReceiptStatus): string {
  switch (status) {
    case "draft":
      return "This Goods Receipt is a saved draft and has not yet entered physical receiving.";
    case "receiving":
      return "Physical receiving is in progress. The receipt remains editable until receiving is completed.";
    case "received":
      return "Physical receiving is complete. The receipt is awaiting review or approval.";
    case "under_review":
      return "The receipt is under review before approval.";
    case "approved":
      return "The receipt has been approved and is ready for posting to inventory.";
    case "posted":
      return "The receipt has been posted to inventory. Stock movements are now part of the inventory ledger.";
    case "cancelled":
      return "The receipt has been cancelled and cannot continue through the receiving lifecycle.";
  }
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
            Review receiving evidence, lifecycle status, reconciliation, and inventory posting.
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
              description="Open a Goods Receipt to review its receiving and posting status."
            />
          </PageSection>
        ) : receiptQuery.isLoading ? (
          <PageSection>
            <LoadingState title="Loading Goods Receipt" />
          </PageSection>
        ) : receiptQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Goods Receipt unavailable"
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
  const authorization = useAuthorization();

  const reviewReceipt = useReviewGoodsReceipt();
  const approveReceipt = useApproveGoodsReceipt();
  const cancelReceipt = useCancelGoodsReceipt();
  const postReceipt = usePostGoodsReceipt();

  const [
    cancelDialogOpen,
    setCancelDialogOpen,
  ] = useState(false);

  const [
    postDialogOpen,
    setPostDialogOpen,
  ] = useState(false);

  const canReceive = authorization.can("inventory.receive");
  const canApprove = authorization.can("inventory.approve");
  const canPost = authorization.can("inventory.post");

  const isPending =
    reviewReceipt.isPending ||
    approveReceipt.isPending ||
    cancelReceipt.isPending ||
    postReceipt.isPending;

  const isEditable =
    receipt.status === "draft" ||
    receipt.status === "receiving";

  const canReview =
    canApprove &&
    receipt.status === "received";

  const canApproveReceipt =
    canApprove &&
    (
      receipt.status === "received" ||
      receipt.status === "under_review"
    );

  const canCancel =
    canApprove &&
    receipt.status !== "posted" &&
    receipt.status !== "cancelled";

  const canPostReceipt =
    canPost &&
    receipt.status === "approved";

  const handleReview = async () => {
    try {
      await reviewReceipt.mutateAsync(receipt.id);
      toast.success("Goods Receipt placed under review.");
    } catch (error) {
      toast.error(errorMessage(error));
    }
  };

  const handleApprove = async () => {
    try {
      await approveReceipt.mutateAsync(receipt.id);
      toast.success("Goods Receipt approved.");
    } catch (error) {
      toast.error(errorMessage(error));
    }
  };

  const handleCancel = async () => {
    try {
      await cancelReceipt.mutateAsync(receipt.id);
      setCancelDialogOpen(false);
      toast.success("Goods Receipt cancelled.");
    } catch (error) {
      toast.error(errorMessage(error));
    }
  };

  const handlePost = async () => {
    try {
      await postReceipt.mutateAsync(receipt.id);
      setPostDialogOpen(false);
      toast.success("Goods Receipt posted to inventory.");
    } catch (error) {
      toast.error(errorMessage(error));
    }
  };

  return (
    <>
      <PageSection>
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <div className="text-lg font-semibold">
                {receipt.receipt_number}
              </div>

              <Badge variant="outline">
                {statusLabel(receipt.status)}
              </Badge>
            </div>

            <p className="max-w-3xl text-sm text-muted-foreground">
              {lifecycleDescription(receipt.status)}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {canReceive && isEditable ? (
              <Link
                to={PATHS.INVENTORY.resumeReceipt(receipt.id)}
                className={buttonVariants({
                  variant: "outline",
                })}
              >
                <PackagePlus />
                Resume Receiving
              </Link>
            ) : null}

            {canReview ? (
              <Button
                type="button"
                variant="outline"
                onClick={handleReview}
                disabled={isPending}
              >
                <ClipboardCheck />
                Mark Under Review
              </Button>
            ) : null}

            {canApproveReceipt ? (
              <Button
                type="button"
                onClick={handleApprove}
                disabled={isPending}
              >
                <CheckCircle2 />
                Approve
              </Button>
            ) : null}

            {canPostReceipt ? (
              <Button
                type="button"
                onClick={() => setPostDialogOpen(true)}
                disabled={isPending}
              >
                <PackageCheck />
                Post to Inventory
              </Button>
            ) : null}

            {canCancel ? (
              <Button
                type="button"
                variant="destructive"
                onClick={() => setCancelDialogOpen(true)}
                disabled={isPending}
              >
                <XCircle />
                Cancel Receipt
              </Button>
            ) : null}
          </div>
        </div>
      </PageSection>

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
            value={
              <Badge variant="outline">
                {statusLabel(receipt.status)}
              </Badge>
            }
          />

          <DetailBlock
            label="Supplier Reference"
            value={receipt.supplier_reference ?? "None"}
          />

          <DetailBlock
            label="Supplier Invoice"
            value={receipt.supplier_invoice_number ?? "None"}
          />

          <DetailBlock
            label="Invoice Date"
            value={dateLabel(receipt.supplier_invoice_date)}
          />

          <DetailBlock
            label="Payment Terms"
            value={receipt.payment_terms ?? "None"}
          />

          <DetailBlock
            label="Currency"
            value={receipt.invoice_currency ?? "KES"}
          />

          <DetailBlock
            label="Supplier Total"
            value={money(receipt.supplier_invoice_total)}
          />

          <DetailBlock
            label="Calculated Total"
            value={money(receipt.calculated_total)}
          />

          <DetailBlock
            label="Difference"
            value={money(receipt.reconciliation_difference)}
          />

          <DetailBlock
            label="Notes"
            value={receipt.notes ?? "None"}
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="mb-4">
          <h2 className="text-base font-semibold">
            Receiving Lifecycle
          </h2>
          <p className="text-sm text-muted-foreground">
            Operational milestones recorded against this Goods Receipt.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <LifecycleBlock
            label="Receiving Started"
            timestamp={receipt.receiving_started_at}
            actor={receipt.receiving_started_by}
          />

          <LifecycleBlock
            label="Receiving Completed"
            timestamp={receipt.received_at}
            actor={
              receipt.received_by?.name ??
              receipt.received_by?.username ??
              receipt.received_by?.id
            }
          />

          <LifecycleBlock
            label="Under Review"
            timestamp={receipt.under_review_at}
            actor={receipt.under_review_by}
          />

          <LifecycleBlock
            label="Approved"
            timestamp={receipt.approved_at}
            actor={receipt.approved_by}
          />

          <LifecycleBlock
            label="Posted"
            timestamp={receipt.posted_at}
            actor={receipt.posted_by}
          />

          <LifecycleBlock
            label="Cancelled"
            timestamp={receipt.cancelled_at}
            actor={receipt.cancelled_by}
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="mb-4">
          <h2 className="text-base font-semibold">
            Receipt Lines
          </h2>
          <p className="text-sm text-muted-foreground">
            Persisted physical receiving evidence for this Goods Receipt.
          </p>
        </div>

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
                <TableCell>
                  {item.line_number}
                </TableCell>

                <TableCell className="whitespace-normal">
                  <div className="font-medium">
                    {item.product.name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {item.product.internal_sku}
                  </div>
                </TableCell>

                <TableCell>
                  {quantity(item.quantity)}
                </TableCell>

                <TableCell>
                  {item.batch?.batch_number ??
                    item.batch_number ??
                    "None"}
                </TableCell>

                <TableCell>
                  {dateLabel(item.manufacture_date)}
                </TableCell>

                <TableCell>
                  {dateLabel(item.expiry_date)}
                </TableCell>

                <TableCell>
                  {money(item.unit_cost)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </PageSection>

      <AlertDialog
        open={cancelDialogOpen}
        onOpenChange={setCancelDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Cancel Goods Receipt?
            </AlertDialogTitle>

            <AlertDialogDescription>
              This will stop the Goods Receipt workflow. A posted
              receipt or a receipt that already carries inventory
              movements cannot be cancelled.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogCancel
              disabled={cancelReceipt.isPending}
            >
              Keep Receipt
            </AlertDialogCancel>

            <AlertDialogAction
              onClick={(event) => {
                event.preventDefault();
                void handleCancel();
              }}
              disabled={cancelReceipt.isPending}
            >
              {cancelReceipt.isPending
                ? "Cancelling..."
                : "Cancel Receipt"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={postDialogOpen}
        onOpenChange={setPostDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Post Goods Receipt to Inventory?
            </AlertDialogTitle>

            <AlertDialogDescription>
              Posting is the inventory mutation boundary. This will
              create or recognize the receipt's inventory movements
              and make the Goods Receipt part of the stock ledger.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogCancel
              disabled={postReceipt.isPending}
            >
              Not Yet
            </AlertDialogCancel>

            <AlertDialogAction
              onClick={(event) => {
                event.preventDefault();
                void handlePost();
              }}
              disabled={postReceipt.isPending}
            >
              {postReceipt.isPending
                ? "Posting..."
                : "Post to Inventory"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function LifecycleBlock({
  label,
  timestamp,
  actor,
}: {
  label: string;
  timestamp?: string | null;
  actor?: string | null;
}) {
  return (
    <div className="space-y-2 rounded-md border p-3">
      <div className="text-xs uppercase text-muted-foreground">
        {label}
      </div>

      <div className="text-sm font-medium">
        {timestamp
          ? dateTimeLabel(timestamp)
          : "Not reached"}
      </div>

      {timestamp && actor ? (
        <div className="break-all text-xs text-muted-foreground">
          Actor: {actor}
        </div>
      ) : null}
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
