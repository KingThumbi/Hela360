import { SidebarItem } from "./SidebarItem";

import {
  SIDEBAR_GROUP_SPACING,
  SIDEBAR_ITEM_SPACING,
} from "@/constants/layout";

import type { NavigationSection } from "@/types/navigation";
import { cn } from "@/lib/utils";

interface SidebarGroupProps {
  section: NavigationSection;
  collapsed?: boolean;
  onNavigate?: () => void;
}

export function SidebarGroup({
  section,
  collapsed = false,
  onNavigate,
}: SidebarGroupProps) {
  const items = section.items;
  const title = section.title.trim();

  if (items.length === 0) {
    return null;
  }

  return (
    <section
      className={cn(
        SIDEBAR_GROUP_SPACING,
        collapsed && "space-y-2",
      )}
    >
      {title && !collapsed ? (
        <header>
          <h2
            className="
              px-3
              text-[10px]
              font-semibold
              uppercase
              tracking-[0.14em]
              text-muted-foreground/80
            "
          >
            {title}
          </h2>
        </header>
      ) : null}

      <div className={SIDEBAR_ITEM_SPACING}>
        {items.map((item) => (
          <SidebarItem
            key={item.id}
            item={item}
            collapsed={collapsed}
            onNavigate={onNavigate}
          />
        ))}
      </div>
    </section>
  );
}

export default SidebarGroup;
