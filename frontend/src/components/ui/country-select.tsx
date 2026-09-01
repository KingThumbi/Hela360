"use client"

import {
  Check,
  ChevronsUpDown,
  X,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";

import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  COUNTRIES,
  canonicalCountryName,
} from "@/lib/countries";
import { cn } from "@/lib/utils";

interface CountrySelectProps {
  id?: string;
  value: string;
  onValueChange: (value: string) => void;
  onBlur?: () => void;
  disabled?: boolean;
  placeholder?: string;
  "aria-invalid"?: boolean;
}

export function CountrySelect({
  id,
  value,
  onValueChange,
  onBlur,
  disabled = false,
  placeholder = "Select country",
  "aria-invalid": ariaInvalid,
}: CountrySelectProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const canonicalValue =
    canonicalCountryName(value);

  const filteredCountries = useMemo(() => {
    const query = search
      .trim()
      .toLocaleLowerCase("en");

    if (!query) {
      return COUNTRIES;
    }

    return COUNTRIES.filter(
      (country) =>
        country.name
          .toLocaleLowerCase("en")
          .includes(query) ||
        country.code
          .toLocaleLowerCase("en")
          .includes(query),
    );
  }, [search]);

  const close = () => {
    setOpen(false);
    setSearch("");
    onBlur?.();
  };

  const selectCountry = (
    countryName: string,
  ) => {
    onValueChange(countryName);
    close();
  };

  const clearCountry = () => {
    onValueChange("");
    close();
  };

  const valueIsInRegistry =
    COUNTRIES.some(
      (country) =>
        country.name === canonicalValue,
    );

  return (
    <Popover
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen);

        if (!nextOpen) {
          setSearch("");
          onBlur?.();
        }
      }}
    >
      <PopoverTrigger asChild>
        <Button
          id={id}
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-invalid={ariaInvalid}
          disabled={disabled}
          className={cn(
            "w-full justify-between font-normal",
            !canonicalValue &&
              "text-muted-foreground",
          )}
        >
          <span className="truncate">
            {canonicalValue || placeholder}
          </span>

          <ChevronsUpDown className="ml-2 size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="start"
        className="w-[min(360px,var(--anchor-width))] p-0"
      >
        <Command>
          <CommandInput
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search country or ISO code..."
            autoFocus
          />

          <CommandList>
            {canonicalValue &&
            !valueIsInRegistry ? (
              <div className="border-b p-2">
                <div className="px-2 py-1 text-xs font-medium text-muted-foreground">
                  Legacy value
                </div>

                <div className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm">
                  <span className="truncate">
                    {canonicalValue}
                  </span>

                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={clearCountry}
                  >
                    <X />
                    Clear
                  </Button>
                </div>
              </div>
            ) : null}

            <CommandEmpty>
              No country matches your search.
            </CommandEmpty>

            <CommandGroup heading="Countries">
              {filteredCountries.map(
                (country) => {
                  const selected =
                    country.name ===
                    canonicalValue;

                  return (
                    <CommandItem
                      key={country.code}
                      value={country.name}
                      aria-selected={selected}
                      onSelect={() =>
                        selectCountry(
                          country.name,
                        )
                      }
                      onKeyDown={(event) => {
                        if (
                          event.key ===
                            "Enter" ||
                          event.key === " "
                        ) {
                          event.preventDefault();

                          selectCountry(
                            country.name,
                          );
                        }
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 size-4",
                          selected
                            ? "opacity-100"
                            : "opacity-0",
                        )}
                      />

                      <span className="min-w-0 flex-1 truncate">
                        {country.name}
                      </span>

                      <span className="ml-3 text-xs text-muted-foreground">
                        {country.code}
                      </span>
                    </CommandItem>
                  );
                },
              )}
            </CommandGroup>
          </CommandList>

          <div className="border-t p-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="w-full justify-start"
              onClick={clearCountry}
            >
              <X />
              No country specified
            </Button>
          </div>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export default CountrySelect;
