import {
  ArrowRightLeft,
} from "lucide-react";

import { Link } from "react-router-dom";

import { PATHS } from "@/routes/routes";
import { cn } from "@/lib/utils";

interface SidebarLogoProps {
  collapsed?: boolean;
}

export function SidebarLogo({
  collapsed = false,
}: SidebarLogoProps) {
  return (
    <Link
      to={PATHS.DASHBOARD}
      className={cn(
        "group flex min-w-0 w-full items-center rounded-lg py-1.5 transition-colors hover:bg-muted/70",
        collapsed
          ? "justify-center px-0"
          : "gap-3 px-2",
      )}
      aria-label={
        collapsed
          ? "Hela360 dashboard"
          : undefined
      }
      title={
        collapsed
          ? "Hela360"
          : undefined
      }
    >
      <div
        className="
          flex
          size-10
          shrink-0
          items-center
          justify-center
          rounded-xl
          bg-[var(--hela-navy)]
          text-white
          shadow-sm
        "
      >
        <ArrowRightLeft className="size-5" />
      </div>

      {!collapsed ? (
        <div className="min-w-0 leading-none">
          <div className="flex items-baseline">
            <span className="text-lg font-bold tracking-tight text-[var(--hela-navy)] dark:text-foreground">
              Hela
            </span>

            <span className="text-lg font-bold tracking-tight text-[var(--hela-gold)]">
              360
            </span>
          </div>

          <div className="mt-1 truncate text-[11px] text-muted-foreground">
            Enterprise ERP
          </div>
        </div>
      ) : null}
    </Link>
  );
}

export default SidebarLogo;
