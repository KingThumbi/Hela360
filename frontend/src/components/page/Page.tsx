import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import { cn } from "@/lib/utils";

export interface PageProps
  extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Page({
  children,
  className,
  ...props
}: PageProps) {
  return (
    <div
      className={cn(
        "flex w-full min-w-0 max-w-full flex-1 flex-col gap-6 overflow-x-hidden lg:gap-8",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export default Page;
