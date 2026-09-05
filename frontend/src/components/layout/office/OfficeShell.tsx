import type { ReactNode } from "react";

import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { OfficeUserMenu } from "./OfficeUserMenu";

import { OfficeSidebar } from "./OfficeSidebar";

export interface OfficeShellProps {
  children?: ReactNode;
}

/**
 * Hela360 Office application shell.
 *
 * The Office shell is intentionally separate from the tenant ERP AppShell.
 * Shared shell primitives may be extracted later once both application
 * compositions are stable.
 */
export function OfficeShell({
  children,
}: OfficeShellProps) {
  return (
    <div
      className="
        flex
        min-h-screen
        w-full
        min-w-0
        overflow-x-hidden
        bg-background
      "
    >
      <OfficeSidebar />

      <div
        className="
          flex
          min-h-screen
          min-w-0
          flex-1
          flex-col
          overflow-x-hidden
        "
      >
        <header
          className="
            sticky
            top-0
            z-30
            flex
            h-16
            shrink-0
            items-center
            justify-between
            border-b
            bg-background/95
            px-6
            backdrop-blur
            supports-[backdrop-filter]:bg-background/80
          "
        >
          <div className="min-w-0">
            <div className="text-sm font-semibold">
              Hela360 Office
            </div>

            <div className="text-xs text-muted-foreground">
              Platform administration
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            <OfficeUserMenu />
          </div>
        </header>

        <main
          className="
            min-h-0
            min-w-0
            flex-1
            overflow-x-hidden
          "
        >
          {children}
        </main>
      </div>
    </div>
  );
}

export default OfficeShell;
