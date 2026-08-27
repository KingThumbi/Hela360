import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * PageToolbar
 * ============================================================================
 *
 * Enterprise page toolbar.
 *
 * Hosts page-level controls such as:
 *
 * • Search
 * • Filters
 * • View selectors
 * • Date ranges
 * • Bulk actions
 * • Export
 * • Refresh
 *
 * The toolbar is purely presentational.
 *
 * Future Integrations
 * -------------------
 * • Sticky toolbar
 * • Saved filters
 * • Density selector
 * • Personalization
 * ============================================================================
 */

export interface PageToolbarProps
  extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function PageToolbar({
  children,
  className,
  ...props
}: PageToolbarProps) {
  return (
    <section
      className={cn(
        "flex flex-col gap-4 rounded-lg border bg-background p-4 lg:flex-row lg:items-center lg:justify-between",
        className,
      )}
      {...props}
    >
      {children}
    </section>
  );
}

export default PageToolbar;