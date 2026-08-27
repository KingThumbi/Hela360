import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * PageTitle
 * ============================================================================
 *
 * Primary heading for an enterprise page.
 *
 * Every Hela360 page should expose exactly one PageTitle.
 * ============================================================================
 */

export interface PageTitleProps
  extends HTMLAttributes<HTMLHeadingElement> {
  children: ReactNode;
}

export function PageTitle({
  children,
  className,
  ...props
}: PageTitleProps) {
  return (
    <h1
      className={cn(
        "text-3xl font-bold tracking-tight",
        className,
      )}
      {...props}
    >
      {children}
    </h1>
  );
}

export default PageTitle;