import { Badge } from "@/components/ui/badge";
import type { NavigationItem } from "@/types/navigation";
import { cn } from "@/lib/utils";
import { NavLink } from "react-router-dom";

interface SidebarItemProps {
  item: NavigationItem;
  collapsed?: boolean;
  onNavigate?: () => void;
}

export function SidebarItem({
  item,
  collapsed = false,
  onNavigate,
}: SidebarItemProps) {
  const Icon = item.icon;

  if (!item.href) {
    return null;
  }

  return (
    <NavLink
      to={item.href}
      end
      aria-disabled={item.disabled}
      aria-label={
        collapsed
          ? item.title
          : undefined
      }
      title={
        collapsed
          ? item.title
          : undefined
      }
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "group flex h-10 items-center rounded-lg px-3 text-sm font-medium transition-all duration-200",
          "hover:bg-accent hover:text-accent-foreground",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          item.disabled &&
            "pointer-events-none cursor-not-allowed opacity-50",
          collapsed
            ? "justify-center px-0"
            : "gap-3",
          isActive && [
            "bg-[var(--hela-navy)]",
            "text-white",
            "shadow-sm",
            "hover:bg-[var(--hela-navy-strong)]",
            "hover:text-white",
          ],
        )
      }
    >
      {Icon ? (
        <Icon className="h-5 w-5 shrink-0" />
      ) : null}

      {!collapsed ? (
        <>
          <span className="flex-1 truncate">
            {item.title}
          </span>

          {item.badge !== undefined &&
          item.badge !== null ? (
            <Badge
              variant="secondary"
              className="ml-auto min-w-5 rounded-full px-1.5 text-[11px]"
            >
              {item.badge}
            </Badge>
          ) : null}
        </>
      ) : null}
    </NavLink>
  );
}

export default SidebarItem;
