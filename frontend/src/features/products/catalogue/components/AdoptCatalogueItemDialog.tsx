import {
  useState,
} from "react";

import {
  Button,
} from "@/components/ui/button";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  Input,
} from "@/components/ui/input";

import {
  Label,
} from "@/components/ui/label";

import type {
  CatalogueItem,
} from "@/types/entities";

import type {
  AdoptCatalogueItemRequest,
} from "@/types/requests";


interface AdoptCatalogueItemDialogProps {
  open: boolean;

  item: CatalogueItem | null;

  isPending: boolean;

  onOpenChange: (
    open: boolean,
  ) => void;

  onSubmit: (
    payload: AdoptCatalogueItemRequest,
  ) => void;
}


function optionalValue(
  value: string,
): string | undefined {
  const normalized = value.trim();

  return normalized.length > 0
    ? normalized
    : undefined;
}


export function AdoptCatalogueItemDialog({
  open,
  item,
  isPending,
  onOpenChange,
  onSubmit,
}: AdoptCatalogueItemDialogProps) {
  const [
    internalSku,
    setInternalSku,
  ] = useState("");

  const [
    name,
    setName,
  ] = useState(
    item?.canonical_name ?? "",
  );

  const [
    categoryName,
    setCategoryName,
  ] = useState(
    item?.category_name ?? "",
  );

  const [
    brandName,
    setBrandName,
  ] = useState(
    item?.brand_name ?? "",
  );

  const [
    unitCode,
    setUnitCode,
  ] = useState("");

  const [
    unitName,
    setUnitName,
  ] = useState("");

  const [
    validationError,
    setValidationError,
  ] = useState<string | null>(null);


  const handleSubmit = (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const hasUnitCode =
      unitCode.trim().length > 0;

    const hasUnitName =
      unitName.trim().length > 0;

    if (hasUnitCode !== hasUnitName) {
      setValidationError(
        "Enter both the unit code and "
        + "unit name, or leave both blank.",
      );

      return;
    }

    setValidationError(null);

    onSubmit({
      internal_sku:
        optionalValue(internalSku),

      name:
        optionalValue(name),

      category_name:
        optionalValue(categoryName),

      brand_name:
        optionalValue(brandName),

      unit_code:
        optionalValue(unitCode),

      unit_name:
        optionalValue(unitName),
    });
  };


  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            Add to Products
          </DialogTitle>

          <DialogDescription>
            {item
              ? `Create a Product from ${item.canonical_name}.`
              : "Create a Product from this catalogue item."}
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit}
          className="space-y-5"
        >
          <div className="rounded-lg border bg-muted/30 p-4">
            <p className="font-medium">
              {item?.canonical_name ??
                "Catalogue item"}
            </p>

            <p className="mt-1 text-sm text-muted-foreground">
              {[
                item?.generic_name,
                item?.strength,
                item?.dosage_form,
              ]
                .filter(Boolean)
                .join(" · ") ||
                item?.master_code}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="catalogue-product-name">
                Product name
              </Label>

              <Input
                id="catalogue-product-name"
                value={name}
                onChange={(event) =>
                  setName(
                    event.target.value,
                  )
                }
                placeholder={
                  item?.canonical_name ??
                  "Product name"
                }
              />

              <p className="text-xs text-muted-foreground">
                You may adjust how this item
                appears in your Product catalogue.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="catalogue-sku">
                Internal SKU
              </Label>

              <Input
                id="catalogue-sku"
                value={internalSku}
                onChange={(event) =>
                  setInternalSku(
                    event.target.value,
                  )
                }
                placeholder="Leave blank to generate"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="catalogue-brand">
                Brand
              </Label>

              <Input
                id="catalogue-brand"
                value={brandName}
                onChange={(event) =>
                  setBrandName(
                    event.target.value,
                  )
                }
                placeholder="Optional"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="catalogue-category">
                Category
              </Label>

              <Input
                id="catalogue-category"
                value={categoryName}
                onChange={(event) =>
                  setCategoryName(
                    event.target.value,
                  )
                }
                placeholder="Optional"
              />
            </div>

            <div />

            <div className="space-y-2">
              <Label htmlFor="catalogue-unit-code">
                Unit code
              </Label>

              <Input
                id="catalogue-unit-code"
                value={unitCode}
                onChange={(event) =>
                  setUnitCode(
                    event.target.value,
                  )
                }
                placeholder="e.g. TAB"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="catalogue-unit-name">
                Unit name
              </Label>

              <Input
                id="catalogue-unit-name"
                value={unitName}
                onChange={(event) =>
                  setUnitName(
                    event.target.value,
                  )
                }
                placeholder="e.g. Tablet"
              />
            </div>
          </div>

          {validationError ? (
            <p className="text-sm text-destructive">
              {validationError}
            </p>
          ) : null}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={isPending}
              onClick={() =>
                onOpenChange(false)
              }
            >
              Cancel
            </Button>

            <Button
              type="submit"
              disabled={
                isPending || !item
              }
            >
              {isPending
                ? "Adding Product..."
                : "Add Product"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}


export default AdoptCatalogueItemDialog;
