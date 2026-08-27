import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { useTheme } from "@/hooks/useTheme";

/**
 * ============================================================================
 * ThemeToggle
 * ============================================================================
 *
 * Enterprise theme selector.
 *
 * Responsibilities
 * ----------------
 * • Display the current application theme
 * • Allow switching between Light, Dark and System themes
 * • Reflect the resolved theme visually
 * • Delegate all business logic to useTheme()
 *
 * This component intentionally contains no theme management logic.
 * Theme persistence, system preference detection and document updates are
 * handled exclusively by useTheme().
 *
 * Future Integrations
 * -------------------
 * • Persist theme to backend user preferences
 * • Tenant-wide branding
 * • Accessibility themes
 * • High contrast mode
 * • Dynamic enterprise themes
 * • Seasonal themes
 * ============================================================================
 */

export function ThemeToggle() {
  const {
    theme,
    resolvedTheme,
    setTheme,
  } = useTheme();

  const icon =
    resolvedTheme === "dark" ? (
      <Moon className="h-5 w-5" />
    ) : (
      <Sun className="h-5 w-5" />
    );

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Change theme"
        >
          {icon}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        className="w-44"
      >
        <DropdownMenuItem
          onClick={() => setTheme("light")}
          disabled={theme === "light"}
        >
          <Sun className="mr-2 h-4 w-4" />
          <span>Light</span>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => setTheme("dark")}
          disabled={theme === "dark"}
        >
          <Moon className="mr-2 h-4 w-4" />
          <span>Dark</span>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={() => setTheme("system")}
          disabled={theme === "system"}
        >
          <span className="mr-2 text-base">💻</span>
          <span>System</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default ThemeToggle;