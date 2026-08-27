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

import { useTenant } from "@/hooks/useTenant";
import { cn } from "@/lib/utils";

/**
 * ============================================================================
 * TenantSelector
 * ============================================================================
 *
 * Enterprise tenant selector.
 *
 * Responsibilities
 * ----------------
 * • Display the active tenant
 * • Allow tenant switching (platform users)
 * • Provide searchable tenant selection
 * • Integrate with the authenticated Identity
 *
 * This component intentionally contains no tenant business logic.
 * All state is provided by useTenant().
 *
 * Future Integrations
 * -------------------
 * • Platform Administration
 * • Super Administrator
 * • Multi-tenant switching
 * • Tenant provisioning
 * • Recently accessed tenants
 * • Tenant favourites
 * • Tenant logos
 * • Cross-tenant authorization
 *
 * Notes
 * -----
 * • Most tenant users will only ever see one tenant.
 * • Platform administrators may switch between tenants.
 * ============================================================================
 */

export function TenantSelector() {
  const {
    tenant,
    tenants,
    canSwitchTenant,
    isOpen,
    open,
    close,
    setTenant,
  } = useTenant();

  if (!tenant) {
    return null;
  }

  if (!canSwitchTenant) {
    return (
      <Button
        variant="ghost"
        className="justify-start gap-2 px-2"
        disabled
      >
        <Building2 className="h-4 w-4" />

        <span className="truncate">
          {tenant.name}
        </span>
      </Button>
    );
  }

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
          <span className="flex items-center gap-2 truncate">
            <Building2 className="h-4 w-4 shrink-0" />

            <span className="truncate">
              {tenant.name}
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
        className="w-64 p-0"
        align="start"
      >
        <Command>
          <CommandInput placeholder="Search tenants..." />

          <CommandList>
            <CommandEmpty>
              No tenants found.
            </CommandEmpty>

            <CommandGroup>
              {tenants.map((item) => (
                <CommandItem
                  key={item.id}
                  value={item.name}
                  onSelect={() => {
                    setTenant(item.id);
                    close();
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      item.id === tenant.id
                        ? "opacity-100"
                        : "opacity-0",
                    )}
                  />

                  <Building2 className="mr-2 h-4 w-4 text-muted-foreground" />

                  <span className="truncate">
                    {item.name}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export default TenantSelector;
