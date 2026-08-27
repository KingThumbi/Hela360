import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

export interface PageContentProps
  extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
}

export function PageContent({
  children,
  className,
  ...props
}: PageContentProps) {
  return (
    <section
      className={cn(
        "flex w-full min-w-0 max-w-full flex-1 flex-col gap-4 overflow-x-hidden sm:gap-5 lg:gap-6",
        className,
      )}
      {...props}
    >
      {children}
    </section>
  );
}

export default PageContent;
