import {
  Search,
} from "lucide-react";
import {
  useMemo,
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
import {
  useProducts,
} from "@/hooks/queries/products";
import type {
  Product,
  StockCountScopeProduct,
} from "@/types/entities";


const PRODUCT_PAGE_SIZE = 10;


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


function productLabel(product: Product): string {
  return `${product.internal_sku} - ${product.name}`;
}


interface AddDiscoveredStockDialogProps {
  countId: string;

  scopeType: "full" | "selected";

  scopeProducts: StockCountScopeProduct[];

  open: boolean;

  onOpenChange: (open: boolean) => void;

  onCreated: () => void;
}


export function AddDiscoveredStockDialog({
  countId,
  scopeType,
  scopeProducts,
  open,
  onOpenChange,
  onCreated,
}: AddDiscoveredStockDialogProps) {
  const [
    productSearchInput,
    setProductSearchInput,
  ] = useState("");

  const [
    productSearch,
    setProductSearch,
  ] = useState("");

  const [
    selectedProductId,
    setSelectedProductId,
  ] = useState("");

  const [
    batchNumber,
    setBatchNumber,
  ] = useState("");

  const [
    expiryDate,
    setExpiryDate,
  ] = useState("");

  const [
    countedQuantity,
    setCountedQuantity,
  ] = useState("");

  const [
    notes,
    setNotes,
  ] = useState("");

  const productsQuery = useProducts(
    {
      page: 1,
      per_page: PRODUCT_PAGE_SIZE,
      search: productSearch || undefined,
      is_active: true,
    },
    {
      enabled: open,
    },
  );

  const addDiscoveredItem =
    useAddDiscoveredStockCountItem();

  const allowedProductIds = useMemo(
    () =>
      scopeType === "selected"
        ? new Set(
            scopeProducts.map(
              (scopeProduct) =>
                scopeProduct.product.id,
            ),
          )
        : null,
    [
      scopeProducts,
      scopeType,
    ],
  );

  const eligibleProducts = useMemo(
    () =>
      (productsQuery.data?.items ?? []).filter(
        (product) =>
          product.is_active &&
          product.track_inventory &&
          (
            allowedProductIds === null ||
            allowedProductIds.has(product.id)
          ),
      ),
    [
      allowedProductIds,
      productsQuery.data?.items,
    ],
  );

  const selectedProduct = useMemo(
    () =>
      eligibleProducts.find(
        (product) =>
          product.id === selectedProductId,
      ),
    [
      eligibleProducts,
      selectedProductId,
    ],
  );

  const resetForm = () => {
    setProductSearchInput("");
    setProductSearch("");
    setSelectedProductId("");
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

  const searchProducts = () => {
    setProductSearch(
      productSearchInput.trim(),
    );
    setSelectedProductId("");
  };

  const submit = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!selectedProduct) {
      toast.error(
        "Select the Product physically found.",
      );
      return;
    }

    const quantity = countedQuantity.trim();

    if (!decimalInputIsValid(quantity)) {
      toast.error(
        "Physical Count must be a non-negative decimal.",
      );
      return;
    }

    const batch = batchNumber.trim();
    const expiry = expiryDate.trim();

    if (
      selectedProduct.track_batches &&
      !batch
    ) {
      toast.error(
        "Enter the observed Batch Number for this Product.",
      );
      return;
    }

    if (
      selectedProduct.track_expiry &&
      !expiry
    ) {
      toast.error(
        "Enter the observed Expiry Date for this Product.",
      );
      return;
    }

    addDiscoveredItem.mutate(
      {
        countId,
        payload: {
          product_id: selectedProduct.id,
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
            "Discovered stock recorded.",
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
              Record Discovered Stock
            </DialogTitle>

            <DialogDescription>
              Record stock physically found during
              this count that is not already represented
              by an existing count line. System stock
              quantities remain concealed during a blind
              count.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <Field label="Find Product">
              <div className="flex gap-2">
                <Input
                  type="search"
                  value={productSearchInput}
                  onChange={(event) =>
                    setProductSearchInput(
                      event.target.value,
                    )
                  }
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter"
                    ) {
                      event.preventDefault();
                      searchProducts();
                    }
                  }}
                  placeholder="Search Product or SKU"
                  disabled={
                    addDiscoveredItem.isPending
                  }
                />

                <Button
                  type="button"
                  variant="outline"
                  onClick={searchProducts}
                  disabled={
                    addDiscoveredItem.isPending
                  }
                >
                  <Search />
                  Search
                </Button>
              </div>
            </Field>

            <Field label="Product">
              <NativeSelect
                value={selectedProductId}
                onChange={(value) => {
                  setSelectedProductId(value);
                  setBatchNumber("");
                  setExpiryDate("");
                }}
                placeholder={
                  productsQuery.isLoading
                    ? "Loading Products"
                    : scopeType === "selected"
                      ? "Select a Product in this count"
                      : "Select inventory Product"
                }
                options={eligibleProducts.map(
                  (product) => ({
                    value: product.id,
                    label: productLabel(
                      product,
                    ),
                  }),
                )}
                disabled={
                  addDiscoveredItem.isPending
                }
              />

              {productsQuery.isError ? (
                <div className="text-sm text-destructive">
                  {errorMessage(
                    productsQuery.error,
                  )}
                </div>
              ) : null}

              {selectedProduct ? (
                <div className="flex flex-wrap gap-2 rounded-md border bg-muted/20 p-3">
                  <div className="mr-auto">
                    <div className="font-medium">
                      {selectedProduct.name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {
                        selectedProduct.internal_sku
                      }
                    </div>
                  </div>

                  {selectedProduct.track_batches ? (
                    <Badge variant="outline">
                      Batch tracked
                    </Badge>
                  ) : null}

                  {selectedProduct.track_expiry ? (
                    <Badge variant="outline">
                      Expiry tracked
                    </Badge>
                  ) : null}
                </div>
              ) : null}
            </Field>

            {selectedProduct?.track_batches ? (
              <Field label="Observed Batch Number">
                <Input
                  value={batchNumber}
                  onChange={(event) =>
                    setBatchNumber(
                      event.target.value,
                    )
                  }
                  placeholder="Enter physical batch number"
                  disabled={
                    addDiscoveredItem.isPending
                  }
                />
              </Field>
            ) : null}

            {selectedProduct?.track_expiry ? (
              <Field label="Observed Expiry Date">
                <Input
                  type="date"
                  value={expiryDate}
                  onChange={(event) =>
                    setExpiryDate(
                      event.target.value,
                    )
                  }
                  disabled={
                    addDiscoveredItem.isPending
                  }
                />
              </Field>
            ) : null}

            <Field label="Physical Count">
              <Input
                inputMode="decimal"
                value={countedQuantity}
                onChange={(event) =>
                  setCountedQuantity(
                    event.target.value,
                  )
                }
                placeholder="Enter quantity physically found"
                disabled={
                  addDiscoveredItem.isPending
                }
              />

              <div className="text-xs text-muted-foreground">
                Enter 0 only when the physical
                observation is genuinely zero.
              </div>
            </Field>

            <Field label="Notes">
              <Textarea
                value={notes}
                onChange={(event) =>
                  setNotes(
                    event.target.value,
                  )
                }
                placeholder="Optional observation notes"
                disabled={
                  addDiscoveredItem.isPending
                }
              />
            </Field>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                handleOpenChange(false)
              }
              disabled={
                addDiscoveredItem.isPending
              }
            >
              Cancel
            </Button>

            <Button
              type="submit"
              disabled={
                addDiscoveredItem.isPending ||
                !selectedProduct
              }
            >
              {addDiscoveredItem.isPending
                ? "Recording..."
                : "Record Discovered Stock"}
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


function NativeSelect({
  value,
  onChange,
  options,
  placeholder,
  disabled = false,
}: {
  value: string;

  onChange: (value: string) => void;

  options: Array<{
    value: string;
    label: string;
  }>;

  placeholder: string;

  disabled?: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(event) =>
        onChange(event.target.value)
      }
      disabled={disabled}
      className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-50"
    >
      <option value="">
        {placeholder}
      </option>

      {options.map((option) => (
        <option
          key={option.value}
          value={option.value}
        >
          {option.label}
        </option>
      ))}
    </select>
  );
}


export default AddDiscoveredStockDialog;
