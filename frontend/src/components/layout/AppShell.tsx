import type { ReactNode } from "react";

import { AppFooter } from "./AppFooter";
import { AppSidebar } from "./AppSidebar";
import {
  AppShellProvider,
} from "./AppShellProvider";
import { AppTopbar } from "./AppTopbar";
import { AppWorkspace } from "./AppWorkspace";

import {
  FOOTER_HEIGHT,
  TOPBAR_HEIGHT,
  Z_INDEX,
} from "@/constants/layout";

export interface AppShellProps {
  children?: ReactNode;
}

function AppShellLayout({
  children,
}: AppShellProps) {
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
      <AppSidebar />

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
            shrink-0
            border-b
            bg-background/95
            backdrop-blur
            supports-[backdrop-filter]:bg-background/80
          "
          style={{
            height: TOPBAR_HEIGHT,
            zIndex: Z_INDEX.TOPBAR,
          }}
        >
          <AppTopbar />
        </header>

        <main
          className="
            flex
            min-h-0
            min-w-0
            flex-1
            overflow-x-hidden
          "
        >
          <AppWorkspace>
            {children}
          </AppWorkspace>
        </main>

        <footer
          className="
            shrink-0
            border-t
            bg-background
          "
          style={{
            minHeight: FOOTER_HEIGHT,
          }}
        >
          <AppFooter />
        </footer>
      </div>
    </div>
  );
}

export function AppShell({
  children,
}: AppShellProps) {
  return (
    <AppShellProvider>
      <AppShellLayout>
        {children}
      </AppShellLayout>
    </AppShellProvider>
  );
}

export default AppShell;
