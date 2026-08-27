import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * PageHeader
 * ============================================================================
 *
 * Enterprise page header.
 *
 * Provides the standard header layout used across all Hela360 pages.
 *
 * Typical composition:
 *
 * <PageHeader>
 *     <div>
 *         <PageTitle />
 *         <PageDescription />
 *     </div>
 *
 *     <PageActions />
 * </PageHeader>
 *
 * Responsibilities
 * ----------------
 * • Organize page metadata
 * • Align page actions
 * • Maintain consistent spacing
 *
 * This component contains no business logic.
 * ============================================================================
 */

export interface PageHeaderProps
  extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
}

export function PageHeader({
  children,
  className,
  ...props
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between",
        className,
      )}
      {...props}
    >
      {children}
    </header>
  );
}

export default PageHeader;