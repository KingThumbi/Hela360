import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

import {
  SidebarGroup,
  SidebarLogo,
} from "@/components/navigation";

import { navigation } from "@/navigation";

import {
  SIDEBAR_COLLAPSED_WIDTH,
  SIDEBAR_FOOTER_HEIGHT,
  SIDEBAR_HEADER_HEIGHT,
  SIDEBAR_MOBILE_WIDTH,
  SIDEBAR_WIDTH,
  Z_INDEX,
} from "@/constants/layout";

import { cn } from "@/lib/utils";

import { useAppShell } from "./useAppShell";

function SidebarContent({
  collapsed = false,
  mobile = false,
}: {
  collapsed?: boolean;
  mobile?: boolean;
}) {
  const {
    closeMobileSidebar,
  } = useAppShell();

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header
        className={cn(
          "flex shrink-0 items-center border-b",
          collapsed
            ? "justify-center px-2"
            : "px-3",
        )}
        style={{
          height: SIDEBAR_HEADER_HEIGHT,
        }}
      >
        <div className="min-w-0 flex-1">
          <SidebarLogo
            collapsed={collapsed}
          />
        </div>

        {mobile ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="ml-2 shrink-0"
            onClick={closeMobileSidebar}
            aria-label="Close navigation"
          >
            <X className="size-5" />
          </Button>
        ) : null}
      </header>

      <ScrollArea className="min-h-0 flex-1">
        <nav
          className={cn(
            "py-4",
            collapsed
              ? "space-y-3 px-2"
              : "space-y-5 px-3",
          )}
        >
          {navigation.map((section) => (
            <SidebarGroup
              key={section.id}
              section={section}
              collapsed={collapsed}
              onNavigate={
                mobile
                  ? closeMobileSidebar
                  : undefined
              }
            />
          ))}
        </nav>
      </ScrollArea>

      {!collapsed ? (
        <footer
          className="
            shrink-0
            border-t
            bg-muted/20
            px-4
            py-3
          "
          style={{
            minHeight: SIDEBAR_FOOTER_HEIGHT,
          }}
        >
          <div className="space-y-0.5 text-xs text-muted-foreground">
            <div className="font-semibold text-foreground">
              Hela360 ERP
            </div>

            <div>Enterprise Edition</div>

            <div>v1.0.0</div>
          </div>
        </footer>
      ) : null}
    </div>
  );
}

export function AppSidebar() {
  const {
    sidebarCollapsed,
    mobileSidebarOpen,
    closeMobileSidebar,
  } = useAppShell();

  const desktopWidth =
    sidebarCollapsed
      ? SIDEBAR_COLLAPSED_WIDTH
      : SIDEBAR_WIDTH;

  return (
    <>
      <aside
        className="
          sticky
          top-0
          hidden
          h-screen
          shrink-0
          overflow-hidden
          border-r
          bg-background
          transition-[width,min-width]
          duration-200
          lg:flex
          lg:flex-col
        "
        style={{
          width: desktopWidth,
          minWidth: desktopWidth,
          zIndex: Z_INDEX.SIDEBAR,
        }}
      >
        <SidebarContent
          collapsed={sidebarCollapsed}
        />
      </aside>

      {mobileSidebarOpen ? (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={closeMobileSidebar}
          className="
            fixed
            inset-0
            bg-black/40
            backdrop-blur-[1px]
            lg:hidden
          "
          style={{
            zIndex: Z_INDEX.DRAWER - 1,
          }}
        />
      ) : null}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 flex h-screen flex-col border-r bg-background shadow-xl transition-transform duration-200 lg:hidden",
          mobileSidebarOpen
            ? "translate-x-0"
            : "-translate-x-full",
        )}
        style={{
          width: SIDEBAR_MOBILE_WIDTH,
          maxWidth: "88vw",
          zIndex: Z_INDEX.DRAWER,
        }}
        aria-hidden={!mobileSidebarOpen}
      >
        <SidebarContent mobile />
      </aside>
    </>
  );
}

export default AppSidebar;
