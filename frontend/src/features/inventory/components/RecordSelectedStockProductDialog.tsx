import {
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  useAddDiscoveredStockCountItem,
} from "@/hooks/queries/inventory";
import type {
  StockCountProduct,
} from "@/types/entities";

interface RecordSelectedStockProductDialogProps {
  countId: string;
  product: StockCountProduct;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

function decimalInputIsValid(value: string): boolean {
  if (!value.trim()) {
    return false;
  }

  const number = Number(value);

  return Number.isFinite(number) && number >= 0;
}

export function RecordSelectedStockProductDialog({
  countId,
  product,
  open,
  onOpenChange,
  onCreated,
}: RecordSelectedStockProductDialogProps) {
  const [batchNumber, setBatchNumber] = useState("");
  const [expiryDate, setExpiryDate] = useState("");
  const [countedQuantity, setCountedQuantity] = useState("");
  const [notes, setNotes] = useState("");

  const addDiscoveredItem =
    useAddDiscoveredStockCountItem();

  const resetForm = () => {
    setBatchNumber("");
    setExpiryDate("");
    setCountedQuantity("");
    setNotes("");
  };

  const handleOpenChange = (nextOpen: boolean) => {
    if (addDiscoveredItem.isPending) {
      return;
    }

    if (!nextOpen) {
      resetForm();
    }

    onOpenChange(nextOpen);
  };

  const submit = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const quantity = countedQuantity.trim();

    if (!decimalInputIsValid(quantity)) {
      toast.error(
        "Physical Count must be a non-negative decimal.",
      );
      return;
    }

    const batch = batchNumber.trim();
    const expiry = expiryDate.trim();

    if (product.track_batches && !batch) {
      toast.error(
        "Enter the observed Batch Number.",
      );
      return;
    }

    if (product.track_expiry && !expiry) {
      toast.error(
        "Enter the observed Expiry Date.",
      );
      return;
    }

    addDiscoveredItem.mutate(
      {
        countId,
        payload: {
          product_id: product.id,
          counted_quantity: quantity,
          ...(batch
            ? {
                batch_number: batch,
              }
            : {}),
          ...(expiry
            ? {
                expiry_date: expiry,
              }
            : {}),
          ...(notes.trim()
            ? {
                notes: notes.trim(),
              }
            : {}),
        },
      },
      {
        onSuccess: () => {
          toast.success(
            "Physical stock recorded.",
          );

          resetForm();
          onOpenChange(false);
          onCreated();
        },

        onError: (error) => {
          toast.error(
            errorMessage(error),
          );
        },
      },
    );
  };

  return (
    <Dialog
      open={open}
      onOpenChange={handleOpenChange}
    >
      <DialogContent className="sm:max-w-xl">
        <form
          className="space-y-4"
          onSubmit={submit}
        >
          <DialogHeader>
            <DialogTitle>
              Record Physical Stock
            </DialogTitle>

            <DialogDescription>
              Enter the quantity physically observed for this
              selected Product. This records count evidence only;
              inventory is not changed until the completed count
              is posted as a Stock Adjustment.
            </DialogDescription>
          </DialogHeader>

          <div className="rounded-md border bg-muted/20 p-3">
            <div className="flex flex-wrap items-start gap-2">
              <div className="mr-auto">
                <div className="font-medium">
                  {product.name}
                </div>

                <div className="text-xs text-muted-foreground">
                  {product.internal_sku}
                </div>
              </div>

              {product.track_batches ? (
                <Badge variant="outline">
                  Batch tracked
                </Badge>
              ) : null}

              {product.track_expiry ? (
                <Badge variant="outline">
                  Expiry tracked
                </Badge>
              ) : null}
            </div>
          </div>

          {product.track_batches ? (
            <Field label="Observed Batch Number">
              <Input
                value={batchNumber}
                onChange={(event) =>
                  setBatchNumber(event.target.value)
                }
                placeholder="Enter physical batch number"
                autoComplete="off"
                disabled={addDiscoveredItem.isPending}
              />
            </Field>
          ) : null}

          {product.track_expiry ? (
            <Field label="Observed Expiry Date">
              <Input
                type="date"
                value={expiryDate}
                onChange={(event) =>
                  setExpiryDate(event.target.value)
                }
                disabled={addDiscoveredItem.isPending}
              />
            </Field>
          ) : null}

          <Field label="Physical Count">
            <Input
              inputMode="decimal"
              value={countedQuantity}
              onChange={(event) =>
                setCountedQuantity(event.target.value)
              }
              placeholder="Enter quantity physically found"
              autoFocus
              disabled={addDiscoveredItem.isPending}
            />

            <div className="text-xs text-muted-foreground">
              Enter the physical quantity actually observed.
              Use “Confirm no stock found” instead of recording
              zero when the selected Product is absent.
            </div>
          </Field>

          <Field label="Notes">
            <Textarea
              value={notes}
              onChange={(event) =>
                setNotes(event.target.value)
              }
              placeholder="Optional count observation"
              disabled={addDiscoveredItem.isPending}
            />
          </Field>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                handleOpenChange(false)
              }
              disabled={addDiscoveredItem.isPending}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              disabled={addDiscoveredItem.isPending}
            >
              {addDiscoveredItem.isPending
                ? "Recording..."
                : "Record Physical Stock"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

export default RecordSelectedStockProductDialog;
