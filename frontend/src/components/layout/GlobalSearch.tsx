import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

/**
 * ============================================================================
 * GlobalSearch
 * ============================================================================
 *
 * Enterprise application search.
 *
 * Responsibilities
 * ----------------
 * • Render the global search entry point
 * • Provide a consistent search experience throughout the application
 * • Act as the future trigger for the enterprise Command Palette
 *
 * This component intentionally contains no search business logic.
 *
 * Future Integrations
 * -------------------
 * • Command Palette (Ctrl + K)
 * • Product search
 * • Customer search
 * • Supplier search
 * • Invoice search
 * • Navigation search
 * • Global actions
 * • Recent searches
 * • Saved searches
 * ============================================================================
 */

export interface GlobalSearchProps {
  /**
   * Search placeholder.
   */
  placeholder?: string;

  /**
   * Optional click handler.
   *
   * Later this will open the Command Palette.
   */
  onOpen?: () => void;

  /**
   * Disable interaction.
   */
  disabled?: boolean;
}

export function GlobalSearch({
  placeholder = "Search products, customers, invoices…",
  onOpen,
  disabled = false,
}: GlobalSearchProps) {
  return (
    <div className="relative hidden w-full max-w-md lg:block">
      <Search
        className="
          pointer-events-none
          absolute
          left-3
          top-1/2
          h-4
          w-4
          -translate-y-1/2
          text-muted-foreground
        "
      />

      <Input
        readOnly
        disabled={disabled}
        value=""
        placeholder={placeholder}
        onClick={onOpen}
        className="
          cursor-pointer
          pl-10
          pr-16
        "
      />

      <Button
        type="button"
        variant="ghost"
        size="sm"
        disabled={disabled}
        onClick={onOpen}
        className="
          pointer-events-none
          absolute
          right-2
          top-1/2
          h-7
          -translate-y-1/2
          rounded-md
          border
          bg-muted
          px-2
          text-[11px]
          font-medium
          text-muted-foreground
        "
        tabIndex={-1}
      >
        Ctrl K
      </Button>
    </div>
  );
}

export default GlobalSearch;