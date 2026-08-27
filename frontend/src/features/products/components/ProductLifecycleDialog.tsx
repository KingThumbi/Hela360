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

import type { Product } from "@/types/entities";


interface ProductLifecycleDialogProps {
  product: Product | null;
  isPending: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}


export function ProductLifecycleDialog({
  product,
  isPending,
  onOpenChange,
  onConfirm,
}: ProductLifecycleDialogProps) {
  const action = product?.is_active
    ? "Archive"
    : "Restore";

  return (
    <AlertDialog
      open={Boolean(product)}
      onOpenChange={onOpenChange}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {action} product?
          </AlertDialogTitle>

          <AlertDialogDescription>
            {product?.is_active
              ? "This product will be archived and removed from normal operational use. Existing transactions and historical records remain intact."
              : "This product will be restored to the active catalogue and become available for operational use again."}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel
            disabled={isPending}
          >
            Cancel
          </AlertDialogCancel>

          <AlertDialogAction
            type="button"
            variant={
              product?.is_active
                ? "destructive"
                : "default"
            }
            disabled={isPending}
            onClick={onConfirm}
          >
            {isPending
              ? "Working..."
              : action}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}


export default ProductLifecycleDialog;
