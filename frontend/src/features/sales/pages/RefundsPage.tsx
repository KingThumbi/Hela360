import {
  RotateCcw,
  Search,
} from "lucide-react";
import {
  type FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";
import { toast } from "sonner";

import {
  Page,
  PageContent,
  PageDescription,
  PageHeader,
  PageSection,
  PageTitle,
  PageToolbar,
} from "@/components/page";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import {
  useRefundableSale,
  useRefundSale,
} from "@/hooks/queries/sales";
import {
  useCurrentTillShift,
} from "@/hooks/queries/tills";
import { useQueryScope } from "@/hooks/useQueryScope";
import type {
  Sale,
  SaleItem,
} from "@/types/entities";

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

function decimalValue(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === "") {
    return 0;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function money(value: number): string {
  return value.toFixed(2);
}

function itemLabel(item: SaleItem): string {
  return item.product_name || item.sku || item.product_id || item.id;
}

export function RefundsPage() {
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const [
    saleLookupInput,
    setSaleLookupInput,
  ] = useState("");
  const [
    submittedSaleLookup,
    setSubmittedSaleLookup,
  ] = useState("");
  const [
    quantities,
    setQuantities,
  ] = useState<Record<string, string>>({});
  const [
    reason,
    setReason,
  ] = useState("");
  const [
    confirmationOpen,
    setConfirmationOpen,
  ] = useState(false);
  const [
    lastRefund,
    setLastRefund,
  ] = useState<{
    id: string;
    number: string;
    amount: string;
  } | null>(null);

  const saleQuery = useRefundableSale(
    submittedSaleLookup,
    {
      enabled: submittedSaleLookup.trim().length > 0,
    },
  );
  const currentShiftQuery = useCurrentTillShift();
  const refundSale = useRefundSale();
  const sale: Sale | null = saleQuery.data ?? null;
  const currentShift = currentShiftQuery.data ?? null;

  useEffect(() => {
    setQuantities({});
    setLastRefund(null);
  }, [sale?.id]);

  const refundableItems = useMemo(
    () =>
      (sale?.items ?? []).filter(
        (item) =>
          decimalValue(item.remaining_refundable_quantity) > 0,
      ),
    [sale?.items],
  );

  const selectedItems = refundableItems
    .map((item) => {
      const quantity = decimalValue(quantities[item.id]);
      const remaining = decimalValue(
        item.remaining_refundable_quantity,
      );
      return {
        item,
        quantity,
        remaining,
      };
    })
    .filter(({ quantity }) => quantity > 0);

  const estimatedRefundTotal = selectedItems.reduce(
    (total, { item, quantity }) =>
      total + quantity * decimalValue(item.unit_price),
    0,
  );

  const invalidSelection = selectedItems.find(
    ({ quantity, remaining }) =>
      quantity <= 0 || quantity > remaining,
  );
  const canSubmit =
    Boolean(sale) &&
    Boolean(currentShift) &&
    selectedItems.length > 0 &&
    !invalidSelection &&
    !refundSale.isPending;

  const submitLookup = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedLookup = saleLookupInput.trim();
    if (!normalizedLookup) {
      return;
    }

    setSubmittedSaleLookup(normalizedLookup);
  };

  const updateQuantity = (
    itemId: string,
    value: string,
  ) => {
    setQuantities((current) => ({
      ...current,
      [itemId]: value,
    }));
  };

  const submitRefund = () => {
    if (!sale || !canSubmit) {
      return;
    }

    refundSale.mutate(
      {
        sale_id: sale.id,
        reason: reason.trim() || undefined,
        items: selectedItems.map(({ item, quantity }) => ({
          sale_item_id: item.id,
          quantity: String(quantity),
          return_to_stock: true,
        })),
      },
      {
        onSuccess: (refund) => {
          toast.success("Refund recorded.");
          setLastRefund({
            id: refund.id,
            number: refund.refund_number,
            amount: refund.refund_total_amount,
          });
          setQuantities({});
          setConfirmationOpen(false);
          void saleQuery.refetch();
        },
        onError: (error) => {
          toast.error(error.message);
          setConfirmationOpen(false);
        },
      },
    );
  };

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Refunds</PageTitle>
          <PageDescription>
            Record returned sale quantities against the original transaction.
          </PageDescription>
        </div>
      </PageHeader>

      <PageContent>
        {!isBranchScopeReady ? (
          <Alert>
            <AlertTitle>Branch required</AlertTitle>
            <AlertDescription>
              Select an active branch from the application header.
            </AlertDescription>
          </Alert>
        ) : null}

        {lastRefund ? (
          <Alert>
            <AlertTitle>Refund recorded</AlertTitle>
            <AlertDescription>
              {lastRefund.number || lastRefund.id} was recorded for {lastRefund.amount}. Inventory was restored for stock-tracked items.
            </AlertDescription>
          </Alert>
        ) : null}

        {saleQuery.isError ? (
          <Alert variant="destructive">
            <AlertTitle>Sale lookup failed</AlertTitle>
            <AlertDescription>
              {errorMessage(saleQuery.error)}
            </AlertDescription>
          </Alert>
        ) : null}

        {isBranchScopeReady && !currentShiftQuery.isLoading && !currentShift ? (
          <Alert variant="destructive">
            <AlertTitle>Open till shift required</AlertTitle>
            <AlertDescription>
              Open a till shift before recording operational refunds.
            </AlertDescription>
          </Alert>
        ) : null}

        <PageSection>
          <PageToolbar>
            <form
              className="flex w-full flex-col gap-2 sm:flex-row"
              onSubmit={submitLookup}
            >
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={saleLookupInput}
                  onChange={(event) =>
                    setSaleLookupInput(event.target.value)
                  }
                  placeholder="Sale number or ID"
                  className="pl-8"
                  disabled={!isBranchScopeReady}
                />
              </div>
              <Button
                type="submit"
                disabled={
                  !isBranchScopeReady ||
                  saleQuery.isFetching ||
                  saleLookupInput.trim().length === 0
                }
              >
                <Search className="size-4" />
                Lookup
              </Button>
            </form>
          </PageToolbar>
        </PageSection>

        {sale ? (
          <PageSection>
            <div className="grid gap-3 md:grid-cols-5">
              <SummaryField
                label="Sale"
                value={sale.sale_number || sale.id}
              />
              <SummaryField
                label="Status"
                value={sale.status || "Unknown"}
              />
              <SummaryField
                label="Paid"
                value={sale.paid_amount}
              />
              <SummaryField
                label="Refundable"
                value={sale.refundable_amount}
              />
              <SummaryField
                label="Till shift"
                value={
                  currentShift
                    ? "Open"
                    : "Required"
                }
              />
            </div>

            <div className="overflow-hidden rounded-md border bg-background">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item</TableHead>
                    <TableHead className="text-right">Sold</TableHead>
                    <TableHead className="text-right">Refunded</TableHead>
                    <TableHead className="text-right">Available</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(sale.items ?? []).map((item) => {
                    const remaining = decimalValue(
                      item.remaining_refundable_quantity,
                    );
                    return (
                      <TableRow key={item.id}>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <span className="font-medium">
                              {itemLabel(item)}
                            </span>
                            {remaining <= 0 ? (
                              <Badge variant="secondary">
                                Fully refunded
                              </Badge>
                            ) : null}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          {item.quantity}
                        </TableCell>
                        <TableCell className="text-right">
                          {item.refunded_quantity ?? "0.0000"}
                        </TableCell>
                        <TableCell className="text-right">
                          {item.remaining_refundable_quantity ?? item.quantity}
                        </TableCell>
                        <TableCell className="text-right">
                          <Input
                            value={quantities[item.id] ?? ""}
                            onChange={(event) =>
                              updateQuantity(
                                item.id,
                                event.target.value,
                              )
                            }
                            inputMode="decimal"
                            disabled={remaining <= 0}
                            className="ml-auto w-28 text-right"
                            placeholder="0"
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>

            {refundableItems.length === 0 ? (
              <Alert>
                <AlertTitle>Nothing refundable</AlertTitle>
                <AlertDescription>
                  This sale has no remaining refundable quantities.
                </AlertDescription>
              </Alert>
            ) : null}

            <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
              <div className="space-y-2">
                <Label htmlFor="refund-reason">Reason</Label>
                <Textarea
                  id="refund-reason"
                  value={reason}
                  onChange={(event) =>
                    setReason(event.target.value)
                  }
                  placeholder="Customer return"
                />
              </div>
              <div className="flex flex-col justify-end gap-3">
                <SummaryField
                  label="Estimated refund"
                  value={money(estimatedRefundTotal)}
                />
                <Button
                  type="button"
                  disabled={!canSubmit}
                  onClick={() => setConfirmationOpen(true)}
                >
                  <RotateCcw className="size-4" />
                  Record Refund
                </Button>
              </div>
            </div>
          </PageSection>
        ) : null}
      </PageContent>

      <AlertDialog
        open={confirmationOpen}
        onOpenChange={setConfirmationOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Record refund
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will record a refund and restore the selected quantities to inventory.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={refundSale.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={!canSubmit}
              onClick={submitRefund}
            >
              Record Refund
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Page>
  );
}

function SummaryField({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border bg-background px-3 py-2">
      <div className="text-xs font-medium text-muted-foreground">
        {label}
      </div>
      <div className="truncate text-sm font-semibold">
        {value}
      </div>
    </div>
  );
}

export default RefundsPage;
