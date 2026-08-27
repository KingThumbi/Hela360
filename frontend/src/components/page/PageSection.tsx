import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * PageSection
 * ============================================================================
 *
 * Logical grouping of page content.
 *
 * Large ERP pages should be divided into sections rather than
 * manually adding spacing.
 *
 * Examples
 * --------
 * • Overview
 * • Inventory
 * • Pricing
 * • Audit Trail
 * • Permissions
 * ============================================================================
 */

export interface PageSectionProps
  extends Omit<
    HTMLAttributes<HTMLElement>,
    "title"
  > {
  title?: ReactNode;

  description?: ReactNode;

  children: ReactNode;
}

export function PageSection({
  title,
  description,
  children,
  className,
  ...props
}: PageSectionProps) {
  return (
    <section
      className={cn(
        "space-y-6",
        className,
      )}
      {...props}
    >
      {(title || description) && (
        <header className="space-y-1">
          {title && (
            <h2 className="text-xl font-semibold tracking-tight">
              {title}
            </h2>
          )}

          {description && (
            <p className="text-sm text-muted-foreground">
              {description}
            </p>
          )}
        </header>
      )}

      {children}
    </section>
  );
}

export default PageSection;
