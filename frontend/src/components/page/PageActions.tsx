import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * PageActions
 * ============================================================================
 *
 * Container for page-level actions.
 *
 * Examples
 * --------
 * • Add Product
 * • Export
 * • Import
 * • Print
 * • Refresh
 * • Bulk Actions
 *
 * This component only provides layout.
 * ============================================================================
 */

export interface PageActionsProps
  extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function PageActions({
  children,
  className,
  ...props
}: PageActionsProps) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-start gap-2 lg:justify-end",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export default PageActions;