import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * PageDescription
 * ============================================================================
 *
 * Secondary descriptive text displayed beneath the page title.
 *
 * Should briefly explain the purpose of the page.
 * ============================================================================
 */

export interface PageDescriptionProps
  extends HTMLAttributes<HTMLParagraphElement> {
  children: ReactNode;
}

export function PageDescription({
  children,
  className,
  ...props
}: PageDescriptionProps) {
  return (
    <p
      className={cn(
        "mt-2 max-w-3xl text-sm text-muted-foreground",
        className,
      )}
      {...props}
    >
      {children}
    </p>
  );
}

export default PageDescription;