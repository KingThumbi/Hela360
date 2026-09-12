import {
  Archive,
  Boxes,
  Loader2,
  Pencil,
  Plus,
  RotateCcw,
  X,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import {
  useArchiveProductUnit,
  useCreateProductUnit,
  useProductUnits,
  useRestoreProductUnit,
  useUpdateProductUnit,
} from "@/hooks/queries/products";

import type {
  Product,
  ProductUnit,
} from "@/types/entities";

import type {
  CreateProductUnitRequest,
  UpdateProductUnitRequest,
} from "@/types/requests";


interface ProductUnitsDialogProps {
  product: Product | null;
  onOpenChange: (open: boolean) => void;
}


interface UnitFormState {
  unit_code: string;
  unit_name: string;
  conversion_factor_to_base: string;
  can_receive: boolean;
  can_sell: boolean;
  sale_price: string;
  minimum_sale_price: string;
}


const EMPTY_UNIT_FORM: UnitFormState = {
  unit_code: "",
  unit_name: "",
  conversion_factor_to_base: "",
  can_receive: true,
  can_sell: true,
  sale_price: "",
  minimum_sale_price: "",
};


function nullableDecimal(
  value: string,
): string | null {
  const normalized = value.trim();

  return normalized.length > 0
    ? normalized
    : null;
}


function unitLabel(
  productUnit: ProductUnit,
): string {
  return (
    productUnit.unit?.name ??
    productUnit.unit?.code ??
    "Unnamed unit"
  );
}


function conversionDescription(
  productUnit: ProductUnit,
  baseUnitName: string,
): string {
  if (productUnit.is_base) {
    return `Base unit · ×${productUnit.conversion_factor_to_base}`;
  }

  return (
    `1 ${unitLabel(productUnit)} = ` +
    `${productUnit.conversion_factor_to_base} ${baseUnitName}`
  );
}


export function ProductUnitsDialog({
  product,
  onOpenChange,
}: ProductUnitsDialogProps) {
  const productId = product?.id;

  const unitsQuery = useProductUnits(
    productId,
    {
      enabled: Boolean(product),
    },
  );

  const createMutation =
    useCreateProductUnit();

  const updateMutation =
    useUpdateProductUnit();

  const archiveMutation =
    useArchiveProductUnit();

  const restoreMutation =
    useRestoreProductUnit();

  const [
    adding,
    setAdding,
  ] = useState(false);

  const [
    editingUnitId,
    setEditingUnitId,
  ] = useState<string | null>(null);

  const [
    form,
    setForm,
  ] = useState<UnitFormState>(
    EMPTY_UNIT_FORM,
  );

  const units =
    unitsQuery.data ?? [];

  const baseUnit = useMemo(
    () =>
      units.find(
        (unit) => unit.is_base,
      ) ?? null,
    [units],
  );

  const baseUnitName =
    baseUnit?.unit?.name ??
    baseUnit?.unit?.code ??
    product?.unit?.name ??
    product?.unit?.code ??
    "base units";

  const mutationPending =
    createMutation.isPending ||
    updateMutation.isPending ||
    archiveMutation.isPending ||
    restoreMutation.isPending;

  useEffect(() => {
    if (!product) {
      setAdding(false);
      setEditingUnitId(null);
      setForm(EMPTY_UNIT_FORM);
    }
  }, [product]);

  const resetForm = () => {
    setAdding(false);
    setEditingUnitId(null);
    setForm(EMPTY_UNIT_FORM);
  };

  const beginAdd = () => {
    setEditingUnitId(null);
    setForm(EMPTY_UNIT_FORM);
    setAdding(true);
  };

  const beginEdit = (
    productUnit: ProductUnit,
  ) => {
    setAdding(false);
    setEditingUnitId(productUnit.id);

    setForm({
      unit_code:
        productUnit.unit?.code ?? "",
      unit_name:
        productUnit.unit?.name ?? "",
      conversion_factor_to_base:
        productUnit.conversion_factor_to_base,
      can_receive:
        productUnit.can_receive,
      can_sell:
        productUnit.can_sell,
      sale_price:
        productUnit.sale_price ?? "",
      minimum_sale_price:
        productUnit.minimum_sale_price ?? "",
    });
  };

  const handleCreate = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!product) {
      return;
    }

    const unitCode =
      form.unit_code.trim();

    const unitName =
      form.unit_name.trim();

    const factor =
      form.conversion_factor_to_base.trim();

    if (!unitCode || !unitName) {
      toast.error(
        "Unit code and unit name are required.",
      );
      return;
    }

    if (!factor) {
      toast.error(
        "Conversion factor is required.",
      );
      return;
    }

    const payload: CreateProductUnitRequest = {
      unit_code: unitCode,
      unit_name: unitName,
      conversion_factor_to_base: factor,
      can_receive: form.can_receive,
      can_sell: form.can_sell,
      sale_price:
        nullableDecimal(
          form.sale_price,
        ),
      minimum_sale_price:
        nullableDecimal(
          form.minimum_sale_price,
        ),
    };

    createMutation.mutate(
      {
        productId: product.id,
        data: payload,
      },
      {
        onSuccess: () => {
          toast.success(
            "Product unit added.",
          );
          resetForm();
        },

        onError: (error) => {
          toast.error(error.message);
        },
      },
    );
  };

  const handleUpdate = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (
      !product ||
      !editingUnitId
    ) {
      return;
    }

    const payload: UpdateProductUnitRequest = {
      can_receive: form.can_receive,
      can_sell: form.can_sell,
      sale_price:
        nullableDecimal(
          form.sale_price,
        ),
      minimum_sale_price:
        nullableDecimal(
          form.minimum_sale_price,
        ),
    };

    updateMutation.mutate(
      {
        productId: product.id,
        productUnitId:
          editingUnitId,
        data: payload,
      },
      {
        onSuccess: () => {
          toast.success(
            "Product unit updated.",
          );
          resetForm();
        },

        onError: (error) => {
          toast.error(error.message);
        },
      },
    );
  };

  const handleLifecycle = (
    productUnit: ProductUnit,
  ) => {
    if (!product) {
      return;
    }

    const mutation =
      productUnit.is_active
        ? archiveMutation
        : restoreMutation;

    mutation.mutate(
      {
        productId: product.id,
        productUnitId:
          productUnit.id,
      },
      {
        onSuccess: () => {
          toast.success(
            productUnit.is_active
              ? "Product unit archived."
              : "Product unit restored.",
          );

          if (
            editingUnitId ===
            productUnit.id
          ) {
            resetForm();
          }
        },

        onError: (error) => {
          toast.error(error.message);
        },
      },
    );
  };

  return (
    <Dialog
      open={Boolean(product)}
      onOpenChange={(open) => {
        if (
          !open &&
          !mutationPending
        ) {
          resetForm();
          onOpenChange(false);
        }
      }}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Boxes />
            Units & Pack Sizes
          </DialogTitle>

          <DialogDescription>
            {product
              ? `Manage receiving and selling units for ${product.name}.`
              : "Manage product units."}
          </DialogDescription>
        </DialogHeader>

        {product ? (
          <div className="space-y-6">
            <div className="rounded-lg border bg-muted/30 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Inventory base unit
              </p>

              <p className="mt-1 font-medium">
                {baseUnitName}
              </p>

              <p className="mt-1 text-sm text-muted-foreground">
                Inventory quantities are normalized to this unit.
                Existing conversion factors are locked to protect
                historical transaction meaning.
              </p>
            </div>

            {unitsQuery.isLoading ? (
              <div className="flex items-center gap-2 rounded-lg border p-6 text-sm text-muted-foreground">
                <Loader2 className="animate-spin" />
                Loading product units...
              </div>
            ) : unitsQuery.isError ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                <p className="text-sm text-destructive">
                  {unitsQuery.error instanceof Error
                    ? unitsQuery.error.message
                    : "Unable to load product units."}
                </p>

                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={() =>
                    unitsQuery.refetch()
                  }
                >
                  Retry
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {units.map(
                  (productUnit) => (
                    <div
                      key={productUnit.id}
                      className="rounded-lg border bg-background p-4"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0 space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium">
                              {unitLabel(
                                productUnit,
                              )}
                            </p>

                            {productUnit.is_base ? (
                              <Badge>
                                Base
                              </Badge>
                            ) : null}

                            <Badge
                              variant={
                                productUnit.is_active
                                  ? "secondary"
                                  : "outline"
                              }
                            >
                              {productUnit.is_active
                                ? "Active"
                                : "Archived"}
                            </Badge>
                          </div>

                          <p className="text-sm text-muted-foreground">
                            {conversionDescription(
                              productUnit,
                              baseUnitName,
                            )}
                          </p>

                          <div className="flex flex-wrap gap-2">
                            <Badge variant="outline">
                              Receive{" "}
                              {productUnit.can_receive
                                ? "✓"
                                : "—"}
                            </Badge>

                            <Badge variant="outline">
                              Sell{" "}
                              {productUnit.can_sell
                                ? "✓"
                                : "—"}
                            </Badge>
                          </div>

                          <div className="grid gap-2 text-sm sm:grid-cols-2">
                            <div>
                              <span className="text-muted-foreground">
                                Sale price:{" "}
                              </span>
                              <span>
                                {productUnit.sale_price ??
                                  "Not set"}
                              </span>
                            </div>

                            <div>
                              <span className="text-muted-foreground">
                                Minimum:{" "}
                              </span>
                              <span>
                                {productUnit.minimum_sale_price ??
                                  "Not set"}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex shrink-0 flex-wrap gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            disabled={
                              mutationPending ||
                              !productUnit.is_active
                            }
                            onClick={() =>
                              beginEdit(
                                productUnit,
                              )
                            }
                          >
                            <Pencil />
                            Edit
                          </Button>

                          {!productUnit.is_base ? (
                            <Button
                              type="button"
                              variant={
                                productUnit.is_active
                                  ? "destructive"
                                  : "outline"
                              }
                              size="sm"
                              disabled={
                                mutationPending
                              }
                              onClick={() =>
                                handleLifecycle(
                                  productUnit,
                                )
                              }
                            >
                              {productUnit.is_active ? (
                                <>
                                  <Archive />
                                  Archive
                                </>
                              ) : (
                                <>
                                  <RotateCcw />
                                  Restore
                                </>
                              )}
                            </Button>
                          ) : null}
                        </div>
                      </div>

                      {editingUnitId ===
                      productUnit.id ? (
                        <form
                          className="mt-4 space-y-4 border-t pt-4"
                          onSubmit={
                            handleUpdate
                          }
                        >
                          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            <div className="space-y-2">
                              <Label>
                                Unit
                              </Label>

                              <Input
                                value={
                                  form.unit_name
                                }
                                disabled
                              />
                            </div>

                            <div className="space-y-2">
                              <Label>
                                Conversion
                              </Label>

                              <Input
                                value={
                                  form.conversion_factor_to_base
                                }
                                disabled
                              />

                              <p className="text-xs text-muted-foreground">
                                Locked after creation.
                              </p>
                            </div>

                            <div className="space-y-2">
                              <Label>
                                Sale Price
                              </Label>

                              <Input
                                inputMode="decimal"
                                value={
                                  form.sale_price
                                }
                                disabled={
                                  mutationPending
                                }
                                onChange={(
                                  event,
                                ) =>
                                  setForm(
                                    (current) => ({
                                      ...current,
                                      sale_price:
                                        event
                                          .target
                                          .value,
                                    }),
                                  )
                                }
                              />
                            </div>

                            <div className="space-y-2">
                              <Label>
                                Minimum Sale Price
                              </Label>

                              <Input
                                inputMode="decimal"
                                value={
                                  form.minimum_sale_price
                                }
                                disabled={
                                  mutationPending
                                }
                                onChange={(
                                  event,
                                ) =>
                                  setForm(
                                    (current) => ({
                                      ...current,
                                      minimum_sale_price:
                                        event
                                          .target
                                          .value,
                                    }),
                                  )
                                }
                              />
                            </div>
                          </div>

                          <div className="grid gap-3 rounded-lg border p-3 sm:grid-cols-2">
                            <label className="flex items-center gap-3 text-sm">
                              <input
                                type="checkbox"
                                className="size-4 rounded border-input"
                                checked={
                                  form.can_receive
                                }
                                disabled={
                                  mutationPending
                                }
                                onChange={(
                                  event,
                                ) =>
                                  setForm(
                                    (current) => ({
                                      ...current,
                                      can_receive:
                                        event
                                          .target
                                          .checked,
                                    }),
                                  )
                                }
                              />
                              Available for receiving
                            </label>

                            <label className="flex items-center gap-3 text-sm">
                              <input
                                type="checkbox"
                                className="size-4 rounded border-input"
                                checked={
                                  form.can_sell
                                }
                                disabled={
                                  mutationPending
                                }
                                onChange={(
                                  event,
                                ) =>
                                  setForm(
                                    (current) => ({
                                      ...current,
                                      can_sell:
                                        event
                                          .target
                                          .checked,
                                    }),
                                  )
                                }
                              />
                              Available for selling
                            </label>
                          </div>

                          <div className="flex justify-end gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              disabled={
                                mutationPending
                              }
                              onClick={
                                resetForm
                              }
                            >
                              <X />
                              Cancel
                            </Button>

                            <Button
                              type="submit"
                              disabled={
                                mutationPending
                              }
                            >
                              {updateMutation.isPending ? (
                                <Loader2 className="animate-spin" />
                              ) : null}
                              Save Unit
                            </Button>
                          </div>
                        </form>
                      ) : null}
                    </div>
                  ),
                )}

                {units.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-6 text-center">
                    <p className="font-medium">
                      No product units configured
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Add a receiving or selling unit for this product.
                    </p>
                  </div>
                ) : null}
              </div>
            )}

            {adding ? (
              <form
                className="space-y-4 rounded-lg border bg-muted/20 p-4"
                onSubmit={handleCreate}
              >
                <div>
                  <p className="font-medium">
                    Add Unit / Pack Size
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Define how this unit converts into {baseUnitName}.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="unit-code">
                      Unit Code
                    </Label>

                    <Input
                      id="unit-code"
                      placeholder="e.g. STRIP"
                      value={
                        form.unit_code
                      }
                      disabled={
                        mutationPending
                      }
                      onChange={(event) =>
                        setForm(
                          (current) => ({
                            ...current,
                            unit_code:
                              event.target.value,
                          }),
                        )
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="unit-name">
                      Unit Name
                    </Label>

                    <Input
                      id="unit-name"
                      placeholder="e.g. Strip"
                      value={
                        form.unit_name
                      }
                      disabled={
                        mutationPending
                      }
                      onChange={(event) =>
                        setForm(
                          (current) => ({
                            ...current,
                            unit_name:
                              event.target.value,
                          }),
                        )
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="unit-factor">
                      Conversion to {baseUnitName}
                    </Label>

                    <Input
                      id="unit-factor"
                      inputMode="decimal"
                      placeholder="e.g. 10"
                      value={
                        form.conversion_factor_to_base
                      }
                      disabled={
                        mutationPending
                      }
                      onChange={(event) =>
                        setForm(
                          (current) => ({
                            ...current,
                            conversion_factor_to_base:
                              event.target.value,
                          }),
                        )
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="unit-sale-price">
                      Sale Price
                    </Label>

                    <Input
                      id="unit-sale-price"
                      inputMode="decimal"
                      value={
                        form.sale_price
                      }
                      disabled={
                        mutationPending
                      }
                      onChange={(event) =>
                        setForm(
                          (current) => ({
                            ...current,
                            sale_price:
                              event.target.value,
                          }),
                        )
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="unit-min-price">
                      Minimum Sale Price
                    </Label>

                    <Input
                      id="unit-min-price"
                      inputMode="decimal"
                      value={
                        form.minimum_sale_price
                      }
                      disabled={
                        mutationPending
                      }
                      onChange={(event) =>
                        setForm(
                          (current) => ({
                            ...current,
                            minimum_sale_price:
                              event.target.value,
                          }),
                        )
                      }
                    />
                  </div>
                </div>

                <div className="grid gap-3 rounded-lg border p-3 sm:grid-cols-2">
                  <label className="flex items-center gap-3 text-sm">
                    <input
                      type="checkbox"
                      className="size-4 rounded border-input"
                      checked={
                        form.can_receive
                      }
                      disabled={
                        mutationPending
                      }
                      onChange={(event) =>
                        setForm(
                          (current) => ({
                            ...current,
                            can_receive:
                              event.target.checked,
                          }),
                        )
                      }
                    />
                    Available for receiving
                  </label>

                  <label className="flex items-center gap-3 text-sm">
                    <input
                      type="checkbox"
                      className="size-4 rounded border-input"
                      checked={
                        form.can_sell
                      }
                      disabled={
                        mutationPending
                      }
                      onChange={(event) =>
                        setForm(
                          (current) => ({
                            ...current,
                            can_sell:
                              event.target.checked,
                          }),
                        )
                      }
                    />
                    Available for selling
                  </label>
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={
                      mutationPending
                    }
                    onClick={resetForm}
                  >
                    Cancel
                  </Button>

                  <Button
                    type="submit"
                    disabled={
                      mutationPending
                    }
                  >
                    {createMutation.isPending ? (
                      <Loader2 className="animate-spin" />
                    ) : (
                      <Plus />
                    )}
                    Add Unit
                  </Button>
                </div>
              </form>
            ) : (
              <Button
                type="button"
                variant="outline"
                disabled={
                  mutationPending
                }
                onClick={beginAdd}
              >
                <Plus />
                Add Unit / Pack Size
              </Button>
            )}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}


export default ProductUnitsDialog;
