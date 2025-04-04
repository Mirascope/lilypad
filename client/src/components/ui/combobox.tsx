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
import { cn } from "@/lib/utils";
import { CaretSortIcon, CheckIcon } from "@radix-ui/react-icons";
import { useState } from "react";

interface ComboboxBaseProps {
  items: { value: string; label: string }[];
  popoverText?: string;
  helperText?: string;
  emptyText?: string;
  disabled?: boolean;
  disableAdd?: boolean;
  customTrigger?: React.ReactNode;
}

interface SingleComboboxProps extends ComboboxBaseProps {
  multiple?: false;
  value: string;
  onChange: (value: string) => void;
}

export interface MultipleComboboxProps extends ComboboxBaseProps {
  multiple: true;
  value: string[];
  onChange: (value: string[]) => void;
}

type ComboboxProps = SingleComboboxProps | MultipleComboboxProps;

export function Combobox({
  items,
  value,
  onChange,
  customTrigger,
  popoverText = "Select item...",
  helperText = "Search item...",
  emptyText = "No item found.",
  disabled = false,
  disableAdd = false,
  multiple = false,
}: ComboboxProps) {
  // Type guard to help TypeScript understand our types better
  const isMultiple = multiple === true;
  const [open, setOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");

  // Ensure value is always an array for multiple select
  const safeValue = isMultiple ? (Array.isArray(value) ? value : []) : value;

  const handleSelect = (currentValue: string) => {
    if (multiple) {
      // Type assertion is safe here because we've ensured multiple is true
      const multipleValue = (value as string[]) || [];
      const newValue = [...multipleValue];

      if (newValue.includes(currentValue)) {
        (onChange as (value: string[]) => void)(
          newValue.filter((v) => v !== currentValue)
        );
      } else {
        (onChange as (value: string[]) => void)([...newValue, currentValue]);
      }

      // Don't close when handling multiple selections
    } else {
      // Type assertion is safe here because we've ensured multiple is false
      (onChange as (value: string) => void)(
        currentValue === (value as string) ? "" : currentValue
      );
      setOpen(false);
    }
    setInputValue("");
  };

  const getLabel = (val: string) => {
    const item = items.find((item) => item.value === val);
    return item ? item.label : val;
  };

  const getDisplayValue = () => {
    if (
      !value ||
      (isMultiple && (!Array.isArray(value) || value.length === 0))
    ) {
      return popoverText;
    }

    if (isMultiple) {
      const multipleValue = value as string[];

      if (multipleValue.length === 1) {
        return getLabel(multipleValue[0]);
      }

      return `${getLabel(multipleValue[0])} +${multipleValue.length - 1} more`;
    } else {
      return getLabel(value as string);
    }
  };

  return (
    <div className='flex flex-col gap-2'>
      <Popover open={disabled ? false : open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          {customTrigger ?? (
            <Button
              variant='outline'
              role='combobox'
              aria-expanded={open}
              disabled={disabled}
              className={cn(
                "w-full justify-between",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              {getDisplayValue()}
              <CaretSortIcon className='ml-2 h-4 w-4 shrink-0 opacity-50' />
            </Button>
          )}
        </PopoverTrigger>
        <PopoverContent
          className='p-0 w-[var(--radix-popover-trigger-width)] min-w-[200px]'
          align='start'
          sideOffset={4}
        >
          <Command>
            <CommandInput
              placeholder={helperText}
              value={inputValue}
              onValueChange={setInputValue}
              className='h-9'
            />
            <CommandList>
              <CommandEmpty>{emptyText}</CommandEmpty>
              <CommandGroup>
                {/* Always show selected items first */}
                {isMultiple &&
                  safeValue.length > 0 &&
                  items
                    .filter((item) => safeValue.includes(item.value))
                    .map((item) => (
                      <CommandItem
                        key={`selected-${item.value}`}
                        value={item.value}
                        onSelect={handleSelect}
                      >
                        <CheckIcon className='mr-2 h-4 w-4 opacity-100' />
                        {item.label}
                      </CommandItem>
                    ))}

                {/* Show filtered unselected items */}
                {items
                  .filter((item) => {
                    // For multiple, don't show items again that we've already shown above
                    if (isMultiple && safeValue.includes(item.value)) {
                      return false;
                    }
                    // Filter by search input
                    return item.label
                      .toLowerCase()
                      .includes(inputValue.toLowerCase());
                  })
                  .map((item) => (
                    <CommandItem
                      key={item.value}
                      value={item.value}
                      onSelect={handleSelect}
                    >
                      <CheckIcon
                        className={cn(
                          "mr-2 h-4 w-4",
                          isMultiple
                            ? safeValue.includes(item.value)
                              ? "opacity-100"
                              : "opacity-0"
                            : value === item.value
                              ? "opacity-100"
                              : "opacity-0"
                        )}
                      />
                      {item.label}
                    </CommandItem>
                  ))}
                {inputValue &&
                  !disableAdd &&
                  !items.some(
                    (item) =>
                      item.label.toLowerCase() === inputValue.toLowerCase()
                  ) && (
                    <CommandItem value={inputValue} onSelect={handleSelect}>
                      <CheckIcon
                        className={cn(
                          "mr-2 h-4 w-4",
                          isMultiple
                            ? (value as string[]).includes(inputValue)
                              ? "opacity-100"
                              : "opacity-0"
                            : value === inputValue
                              ? "opacity-100"
                              : "opacity-0"
                        )}
                      />
                      Add &quot;{inputValue}&quot;
                    </CommandItem>
                  )}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
