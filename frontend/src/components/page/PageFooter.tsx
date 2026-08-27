import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * PageFooter
 * ============================================================================
 *
 * Footer displayed at the bottom of a page.
 *
 * Examples
 * --------
 * • Pagination
 * • Totals
 * • Last updated
 * • Bulk actions
 * • Save / Cancel buttons
 *
 * Contains no business logic.
 * ============================================================================
 */

export interface PageFooterProps
  extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
}

export function PageFooter({
  children,
  className,
  ...props
}: PageFooterProps) {
  return (
    <footer
      className={cn(
        "flex flex-col gap-4 border-t pt-6 lg:flex-row lg:items-center lg:justify-between",
        className,
      )}
      {...props}
    >
      {children}
    </footer>
  );
}

export default PageFooter;