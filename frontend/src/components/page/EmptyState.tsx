import type { ReactNode } from "react";

import { Inbox } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * EmptyState
 * ============================================================================
 *
 * Enterprise empty state.
 *
 * Examples
 * --------
 * • No Products
 * • No Customers
 * • No Sales
 * • No Inventory
 * • No Reports
 *
 * Pure presentation component.
 * ============================================================================
 */

export interface EmptyStateProps {
  title: string;

  description?: string;

  actionLabel?: string;

  onAction?: () => void;

  icon?: ReactNode;

  className?: string;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[320px] flex-col items-center justify-center rounded-lg border border-dashed bg-background p-10 text-center",
        className,
      )}
    >
      <div className="mb-4 text-muted-foreground">
        {icon ?? <Inbox className="h-12 w-12" />}
      </div>

      <h2 className="text-xl font-semibold">
        {title}
      </h2>

      {description && (
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          {description}
        </p>
      )}

      {actionLabel && onAction && (
        <Button
          className="mt-6"
          onClick={onAction}
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;