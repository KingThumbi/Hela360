import {
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

import { TOPBAR_HEIGHT } from "@/constants/layout";

import { BranchSelector } from "./BranchSelector";
import { Breadcrumbs } from "./Breadcrumbs";
import { GlobalSearch } from "./GlobalSearch";
import { NotificationMenu } from "./NotificationMenu";
import { ThemeToggle } from "./ThemeToggle";
import { UserMenu } from "./UserMenu";
import { useAppShell } from "./useAppShell";

export function AppTopbar() {
  const {
    sidebarCollapsed,
    toggleSidebar,
    openMobileSidebar,
  } = useAppShell();

  return (
    <div
      className="
        flex
        h-full
        min-w-0
        items-center
        justify-between
        gap-2
        px-3
        sm:gap-3
        sm:px-4
        lg:gap-4
        lg:px-6
      "
      style={{
        minHeight: TOPBAR_HEIGHT,
      }}
    >
      <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3 lg:gap-4">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="shrink-0 lg:hidden"
          onClick={openMobileSidebar}
          aria-label="Open navigation"
        >
          <Menu className="size-5" />
        </Button>

        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="hidden shrink-0 lg:inline-flex"
          onClick={toggleSidebar}
          aria-label={
            sidebarCollapsed
              ? "Expand sidebar"
              : "Collapse sidebar"
          }
          title={
            sidebarCollapsed
              ? "Expand sidebar"
              : "Collapse sidebar"
          }
        >
          {sidebarCollapsed ? (
            <PanelLeftOpen className="size-5" />
          ) : (
            <PanelLeftClose className="size-5" />
          )}
        </Button>

        <div className="min-w-0 shrink">
          <Breadcrumbs />
        </div>

        <Separator
          orientation="vertical"
          className="hidden h-6 lg:block"
        />

        <div className="hidden min-w-0 flex-1 md:block">
          <GlobalSearch />
        </div>
      </div>

      <div className="flex min-w-0 shrink-0 items-center gap-1 sm:gap-2">
        <div className="min-w-0 max-w-[150px] sm:max-w-none">
          <BranchSelector />
        </div>

        <Separator
          orientation="vertical"
          className="hidden h-6 sm:block"
        />

        <div className="hidden sm:block">
          <ThemeToggle />
        </div>

        <div className="hidden sm:block">
          <NotificationMenu />
        </div>

        <UserMenu />
      </div>      
    </div>
  );
}

export default AppTopbar;
