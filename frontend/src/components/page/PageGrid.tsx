import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * PageGrid
 * ============================================================================
 *
 * Standard responsive grid used throughout Hela360.
 *
 * Prevents feature modules from implementing their own grid spacing.
 *
 * Future
 * ------
 * • Density presets
 * • Masonry layouts
 * • User preferences
 * ============================================================================
 */

export interface PageGridProps
  extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;

  columns?: 1 | 2 | 3 | 4;
}

export function PageGrid({
  children,
  columns = 2,
  className,
  ...props
}: PageGridProps) {
  const gridClass = {
    1: "grid-cols-1",
    2: "grid-cols-1 lg:grid-cols-2",
    3: "grid-cols-1 lg:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 xl:grid-cols-4",
  }[columns];

  return (
    <div
      className={cn(
        "grid gap-6",
        gridClass,
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export default PageGrid;