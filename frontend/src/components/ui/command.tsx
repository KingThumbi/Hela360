import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Command({
  className,
  ...props
}: ComponentProps<"div">) {
  return (
    <div
      className={cn("flex flex-col", className)}
      {...props}
    />
  );
}

export function CommandInput({
  className,
  ...props
}: ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "h-9 w-full border-b bg-transparent px-3 text-sm outline-none placeholder:text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}

export function CommandList({
  className,
  ...props
}: ComponentProps<"div">) {
  return (
    <div
      className={cn("max-h-72 overflow-y-auto", className)}
      {...props}
    />
  );
}

export function CommandEmpty({
  className,
  ...props
}: ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "px-3 py-6 text-center text-sm text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}

export function CommandGroup({
  className,
  heading,
  children,
  ...props
}: ComponentProps<"div"> & {
  heading?: string;
}) {
  return (
    <div
      className={cn("p-1", className)}
      {...props}
    >
      {heading && (
        <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
          {heading}
        </div>
      )}

      {children}
    </div>
  );
}

export interface CommandItemProps
  extends Omit<ComponentProps<"div">, "onSelect"> {
  value?: string;
  onSelect?: (value: string) => void;
}

export function CommandItem({
  className,
  value = "",
  onSelect,
  onClick,
  role = "option",
  ...props
}: CommandItemProps) {
  return (
    <div
      className={cn(
        "flex cursor-default items-center rounded-md px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground",
        className,
      )}
      role={role}
      tabIndex={0}
      onClick={(event) => {
        onClick?.(event);
        onSelect?.(value);
      }}
      {...props}
    />
  );
}
