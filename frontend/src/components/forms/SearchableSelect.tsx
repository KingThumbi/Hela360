import { Check, ChevronsUpDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"

export type SearchableSelectOption = {
  value: string
  label: string
  keywords?: string
  disabled?: boolean
}

type SearchableSelectProps = {
  value?: string | null
  onValueChange: (value: string) => void
  options: SearchableSelectOption[]

  placeholder?: string
  searchPlaceholder?: string
  emptyText?: string

  disabled?: boolean
  className?: string
  contentClassName?: string
}

export function SearchableSelect({
  value,
  onValueChange,
  options,
  placeholder = "Select an option",
  searchPlaceholder = "Search...",
  emptyText = "No results found.",
  disabled = false,
  className,
  contentClassName,
}: SearchableSelectProps) {
  const selected = options.find(
    (option) => option.value === value
  )

  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button
            type="button"
            variant="outline"
            role="combobox"
            disabled={disabled}
            className={cn(
              "w-full justify-between font-normal",
              !selected && "text-muted-foreground",
              className
            )}
          />
        }
      >
        <span className="truncate">
          {selected?.label ?? placeholder}
        </span>

        <ChevronsUpDown className="ml-2 size-4 shrink-0 opacity-50" />
      </PopoverTrigger>

      <PopoverContent
        align="start"
        className={cn(
          "w-[var(--anchor-width)] min-w-[18rem] p-0",
          contentClassName
        )}
      >
        <Command>
          <CommandInput
            placeholder={searchPlaceholder}
          />

          <CommandList className="max-h-72 overflow-y-auto overscroll-contain">
            <CommandEmpty>
              {emptyText}
            </CommandEmpty>

            {options.map((option) => (
              <CommandItem
                key={option.value}
                value={`${option.label} ${option.keywords ?? ""}`}
                aria-disabled={option.disabled || undefined}
                className={cn(
                  option.disabled &&
                    "pointer-events-none opacity-50"
                )}
                onSelect={() => {
                  if (!option.disabled) {
                    onValueChange(option.value)
                  }
                }}
              >
                <Check
                  className={cn(
                    "mr-2 size-4",
                    value === option.value
                      ? "opacity-100"
                      : "opacity-0"
                  )}
                />

                <span className="truncate">
                  {option.label}
                </span>
              </CommandItem>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
