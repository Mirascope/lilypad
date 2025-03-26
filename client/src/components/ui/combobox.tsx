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
import { X } from "lucide-react";
import { useState } from "react";

interface ComboboxBaseProps {
  items: { value: string; label: string }[];
  popoverText?: string;
  helperText?: string;
  emptyText?: string;
  disabled?: boolean;
  disableAdd?: boolean;
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

  const handleSelect = (currentValue: string) => {
    if (multiple) {
      // Type assertion is safe here because we've ensured multiple is true
      const newValue = [...(value as string[])];
      if (newValue.includes(currentValue)) {
        (onChange as (value: string[]) => void)(
          newValue.filter((v) => v !== currentValue)
        );
      } else {
        (onChange as (value: string[]) => void)([...newValue, currentValue]);
      }
    } else {
      // Type assertion is safe here because we've ensured multiple is false
      (onChange as (value: string) => void)(
        currentValue === (value as string) ? "" : currentValue
      );
      setOpen(false);
    }
    setInputValue("");
  };

  const handleRemove = (valueToRemove: string) => {
    if (multiple) {
      // Type assertion is safe here because we've ensured multiple is true
      const newValue = (value as string[]).filter((v) => v !== valueToRemove);
      (onChange as (value: string[]) => void)(newValue);
    }
  };

  const getLabel = (val: string) => {
    const item = items.find((item) => item.value === val);
    return item ? item.label : val;
  };

  const getDisplayValue = () => {
    if (!value) return popoverText;

    if (isMultiple) {
      return popoverText;
    } else {
      return getLabel(value as string);
    }
  };

  return (
    <div className='flex flex-col gap-2'>
      <Popover open={disabled ? false : open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
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
        </PopoverTrigger>
        <PopoverContent className='w-full p-0'>
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
                {items
                  .filter((item) =>
                    item.label.toLowerCase().includes(inputValue.toLowerCase())
                  )
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
                            ? (value as string[]).includes(item.value)
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

      {/* Selected Items Pills (only for multiple selection) */}
      {isMultiple && (value as string[]).length > 0 && (
        <div className='flex flex-wrap gap-2'>
          {(value as string[]).map((val) => (
            <div
              key={val}
              className={cn(
                "flex items-center gap-1 rounded-md bg-secondary px-2 py-1 text-sm",
                disabled && "opacity-50"
              )}
            >
              <span>{getLabel(val)}</span>
              {!disabled && (
                <button
                  type='button'
                  onClick={(e) => {
                    e.preventDefault();
                    handleRemove(val);
                  }}
                  className='ml-1 rounded-full hover:bg-destructive/50 p-0.5'
                >
                  <X className='h-3 w-3' />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
