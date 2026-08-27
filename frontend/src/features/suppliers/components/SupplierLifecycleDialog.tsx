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
import type { Supplier } from "@/types/entities";

interface SupplierLifecycleDialogProps {
  supplier: Supplier | null;
  isPending: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function SupplierLifecycleDialog({
  supplier,
  isPending,
  onOpenChange,
  onConfirm,
}: SupplierLifecycleDialogProps) {
  const action = supplier?.is_active
    ? "Deactivate"
    : "Reactivate";

  return (
    <AlertDialog
      open={Boolean(supplier)}
      onOpenChange={onOpenChange}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {action} supplier?
          </AlertDialogTitle>
          <AlertDialogDescription>
            {supplier?.is_active
              ? "This supplier will be marked inactive. Existing records remain intact."
              : "This supplier will be available for operational use again."}
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
              supplier?.is_active
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
