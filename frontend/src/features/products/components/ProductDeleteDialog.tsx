import {
  AlertTriangle,
} from "lucide-react";

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

import type {
  Product,
} from "@/types/entities";


interface ProductDeleteDialogProps {
  product: Product | null;
  isPending: boolean;
  errorMessage: string | null;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}


export function ProductDeleteDialog({
  product,
  isPending,
  errorMessage,
  onOpenChange,
  onConfirm,
}: ProductDeleteDialogProps) {
  return (
    <AlertDialog
      open={Boolean(product)}
      onOpenChange={onOpenChange}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            Permanently delete product?
          </AlertDialogTitle>

          <AlertDialogDescription>
            This will permanently remove{" "}
            {product?.name ?? "this product"} from the
            catalogue.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4">
          <div className="flex gap-3 rounded-lg border p-3">
            <AlertTriangle className="mt-0.5 size-5 shrink-0 text-destructive" />

            <div className="space-y-1 text-sm">
              <p className="font-medium">
                This action cannot be undone.
              </p>

              <p className="text-muted-foreground">
                Products with transaction history,
                inventory history, batches, stock
                movements or other business dependencies
                cannot be permanently deleted. Keep those
                products archived instead.
              </p>
            </div>
          </div>

          {errorMessage ? (
            <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
              {errorMessage}
            </div>
          ) : null}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel
            disabled={isPending}
          >
            Cancel
          </AlertDialogCancel>

          <AlertDialogAction
            type="button"
            variant="destructive"
            disabled={isPending}
            onClick={onConfirm}
          >
            {isPending
              ? "Deleting..."
              : "Delete permanently"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}


export default ProductDeleteDialog;
