import {
  ArrowLeft,
  Shield,
} from "lucide-react";

import {
  Link,
  NavLink,
} from "react-router-dom";

import { cn } from "@/lib/utils";
import { officeNavigation } from "@/navigation/office";
import { OFFICE_PATHS } from "@/routes/officeRoutes";
import { PATHS } from "@/routes/routes";

export function OfficeSidebar() {
  return (
    <aside
      className="
        flex
        min-h-screen
        w-64
        shrink-0
        flex-col
        border-r
        bg-background
      "
    >
      <div className="border-b px-4 py-4">
        <Link
          to={OFFICE_PATHS.DASHBOARD}
          className="
            flex
            items-center
            gap-3
            rounded-lg
            px-2
            py-1.5
            transition-colors
            hover:bg-muted/70
          "
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
            <Shield className="size-5" />
          </div>

          <div className="min-w-0 leading-none">
            <div className="flex items-baseline">
              <span
                className="
                  text-lg
                  font-bold
                  tracking-tight
                  text-[var(--hela-navy)]
                  dark:text-foreground
                "
              >
                Hela
              </span>

              <span
                className="
                  text-lg
                  font-bold
                  tracking-tight
                  text-[var(--hela-gold)]
                "
              >
                360
              </span>
            </div>

            <div
              className="
                mt-1
                text-[11px]
                font-medium
                uppercase
                tracking-[0.16em]
                text-muted-foreground
              "
            >
              Office
            </div>
          </div>
        </Link>
      </div>

      <nav className="flex-1 space-y-5 p-3">
        {officeNavigation.map((section) => (
          <div
            key={section.id}
            className="space-y-1"
          >
            {section.title ? (
              <div
                className="
                  px-3
                  pb-1
                  text-[11px]
                  font-semibold
                  uppercase
                  tracking-[0.12em]
                  text-muted-foreground
                "
              >
                {section.title}
              </div>
            ) : null}

            {section.items.map((item) => {
              const Icon = item.icon;

              return (
                <NavLink
                  key={item.id}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-muted text-foreground"
                        : "text-muted-foreground hover:bg-muted/70 hover:text-foreground",
                    )
                  }
                >
                  <Icon className="size-4 shrink-0" />

                  <span>{item.title}</span>
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="border-t p-3">
        <Link
          to={PATHS.DASHBOARD}
          className="
            flex
            items-center
            gap-3
            rounded-lg
            px-3
            py-2
            text-sm
            font-medium
            text-muted-foreground
            transition-colors
            hover:bg-muted/70
            hover:text-foreground
          "
        >
          <ArrowLeft className="size-4 shrink-0" />

          <span>Open Tenant ERP</span>
        </Link>
      </div>
    </aside>
  );
}

export default OfficeSidebar;
