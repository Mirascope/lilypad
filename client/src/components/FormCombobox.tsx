import { CaretSortIcon, CheckIcon } from "@radix-ui/react-icons";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
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
import { useState } from "react";
import { Control, Controller, FieldValues, Path } from "react-hook-form";

type ComboboxProps<T extends FieldValues> = {
  items: { value: string; label: string }[];
  name: Path<T>;
  control: Control<T>;
  popoverText?: string;
  helperText?: string;
  disabled?: boolean;
};

export const FormCombobox = <T extends FieldValues>({
  items,
  name,
  control,
  popoverText = "Select items...",
  helperText = "Search item...",
  disabled,
}: ComboboxProps<T>) => {
  const [open, setOpen] = useState(false);
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => {
        const [inputValue, setInputValue] = useState("");

        const handleSelect = (currentValue: string) => {
          const newValue = field.value || [];
          if (newValue.includes(currentValue)) {
            field.onChange(
              newValue.filter((value: string) => value !== currentValue)
            );
          } else {
            field.onChange([...newValue, currentValue]);
          }
          setInputValue("");
        };

        const handleRemove = (valueToRemove: string) => {
          field.onChange(
            field.value.filter((value: string) => value !== valueToRemove)
          );
        };

        const getLabel = (value: string) => {
          const item = items.find((item) => item.value === value);
          return item ? item.label : value;
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
                  {popoverText}
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
                    <CommandEmpty>No item found.</CommandEmpty>
                    <CommandGroup>
                      {items
                        .filter((item) =>
                          item.label
                            .toLowerCase()
                            .includes(inputValue.toLowerCase())
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
                                field.value?.includes(item.value)
                                  ? "opacity-100"
                                  : "opacity-0"
                              )}
                            />
                            {item.label}
                          </CommandItem>
                        ))}
                      {inputValue &&
                        !items.some(
                          (item) =>
                            item.label.toLowerCase() ===
                            inputValue.toLowerCase()
                        ) && (
                          <CommandItem
                            value={inputValue}
                            onSelect={handleSelect}
                          >
                            <CheckIcon
                              className={cn(
                                "mr-2 h-4 w-4",
                                field.value?.includes(inputValue)
                                  ? "opacity-100"
                                  : "opacity-0"
                              )}
                            />
                            Add "{inputValue}"
                          </CommandItem>
                        )}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>

            {/* Selected Items Pills */}
            {field.value && field.value.length > 0 && (
              <div className='flex flex-wrap gap-2'>
                {field.value.map((value: string) => (
                  <div
                    key={value}
                    className={cn(
                      "flex items-center gap-1 rounded-md bg-secondary px-2 py-1 text-sm",
                      disabled && "opacity-50"
                    )}
                  >
                    <span>{getLabel(value)}</span>
                    {!disabled && (
                      <button
                        type='button'
                        onClick={(e) => {
                          e.preventDefault();
                          handleRemove(value);
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
      }}
    />
  );
};
