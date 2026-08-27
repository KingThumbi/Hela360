import type { ComponentProps, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

export interface SidebarProviderProps
  extends PropsWithChildren {
  defaultOpen?: boolean;
}

export function SidebarProvider({
  children,
}: SidebarProviderProps) {
  return <>{children}</>;
}

export function SidebarInset({
  className,
  ...props
}: ComponentProps<"div">) {
  return (
    <div
      className={cn("min-w-0 flex-1", className)}
      {...props}
    />
  );
}
