import { Building2, Check, ChevronsUpDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";

import { useCurrentBranch } from "@/hooks/useCurrentBranch";

/**
 * ============================================================================
 * BranchSelector
 * ============================================================================
 *
 * Enterprise branch selector for the Hela360 application shell.
 *
 * Responsibilities
 * ----------------
 * • Display the currently active branch
 * • Allow branch switching
 * • Provide searchable branch selection
 * • Delegate branch state to useCurrentBranch()
 *
 * This component intentionally contains no business logic.
 * All branch resolution, authorization and persistence are handled by
 * useCurrentBranch().
 *
 * Future Integrations
 * -------------------
 * • AuthorizationContext
 * • Branch switching API
 * • Multi-branch permissions
 * • Branch status indicators
 * • Recently used branches
 * • Favorite branches
 * • Branch health
 * • Warehouse affinity
 * • Offline synchronization
 * ============================================================================
 */

export function BranchSelector() {
  const {
    branch,
    branches,
    hasBranch,
    isOpen,
    open,
    close,
    setBranch,
  } = useCurrentBranch();

  return (
    <Popover
      open={isOpen}
      onOpenChange={(value) =>
        value ? open() : close()
      }
    >
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={isOpen}
          className="
            w-64
            justify-between
          "
        >
          <span className="flex items-center gap-2 overflow-hidden">
            <Building2 className="h-4 w-4 shrink-0" />

            <span className="truncate">
              {hasBranch && branch
                ? branch.name
                : "Select Branch"}
            </span>
          </span>

          <ChevronsUpDown
            className="
              ml-2
              h-4
              w-4
              shrink-0
              opacity-50
            "
          />
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="start"
        className="w-64 p-0"
      >
        <Command>
          <CommandInput placeholder="Search branches..." />

          <CommandList>
            <CommandEmpty>
              No branches found.
            </CommandEmpty>

            <CommandGroup heading="Branches">
              {branches.map((item) => {
                const selected =
                  branch?.id === item.id;

                return (
                  <CommandItem
                    key={item.id}
                    value={`${item.code} ${item.name}`}
                    onSelect={() => {
                      setBranch(item.id);
                      close();
                    }}
                  >
                    <Check
                      className={`mr-2 h-4 w-4 ${
                        selected
                          ? "opacity-100"
                          : "opacity-0"
                      }`}
                    />

                    <div className="flex flex-col">
                      <span>{item.name}</span>

                      <span className="text-xs text-muted-foreground">
                        {item.code}
                      </span>
                    </div>
                  </CommandItem>
                );
              })}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export default BranchSelector;