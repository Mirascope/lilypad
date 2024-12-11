import { useEffect, useState } from "react";
import { Control, FieldPath, FieldValues, PathValue } from "react-hook-form";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "@/components/ui/command";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

type Option = {
  value: string;
  label: string;
};

type ModelComboboxProps<T extends FieldValues, TName extends FieldPath<T>> = {
  control: Control<T>;
  name: FieldPath<T>;
  label: string;
  options: Option[];
  defaultValue?: PathValue<T, TName>;
};

export const ModelCombobox = <
  T extends FieldValues,
  TName extends FieldPath<T>,
>({
  control,
  name,
  label,
  options,
  defaultValue,
}: ModelComboboxProps<T, TName>) => {
  return (
    <FormField
      control={control}
      name={name}
      defaultValue={defaultValue}
      render={({ field }) => {
        const [open, setOpen] = useState(false);
        const [inputValue, setInputValue] = useState(field.value || "");

        useEffect(() => {
          if (defaultValue && !field.value) {
            field.onChange(defaultValue);
          }
        }, [defaultValue, field]);

        const handleSelect = (value: string) => {
          field.onChange(value);
          setInputValue(value);
          setOpen(false);
        };

        return (
          <FormItem>
            <FormLabel>{label}</FormLabel>
            <FormControl>
              <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                  <button
                    type='button'
                    className='w-full flex justify-between items-center px-3 py-2 border rounded-md'
                    onClick={() => setOpen(!open)}
                  >
                    {field.value
                      ? options.find((opt) => opt.value === field.value)
                          ?.label || field.value
                      : "Select an option"}
                    <ChevronsUpDown className='h-4 w-4' />
                  </button>
                </PopoverTrigger>
                <PopoverContent className='w-full p-0'>
                  <Command>
                    <CommandInput
                      placeholder='Type or select an option...'
                      value={inputValue}
                      onValueChange={(value) => {
                        setInputValue(value);
                      }}
                    />
                    <CommandList>
                      <CommandEmpty>No results found.</CommandEmpty>
                      <CommandGroup>
                        {options
                          .filter((option) =>
                            option.label
                              .toLowerCase()
                              .includes(inputValue.toLowerCase())
                          )
                          .map((option) => (
                            <CommandItem
                              key={option.value}
                              onSelect={() => handleSelect(option.value)}
                            >
                              <Check
                                className={cn(
                                  "mr-2 h-4 w-4",
                                  field.value === option.value
                                    ? "opacity-100"
                                    : "opacity-0"
                                )}
                              />
                              {option.label}
                            </CommandItem>
                          ))}
                        {inputValue &&
                          !options.some(
                            (opt) =>
                              opt.label.toLowerCase() ===
                              inputValue.toLowerCase()
                          ) && (
                            <CommandItem
                              onSelect={() => handleSelect(inputValue)}
                            >
                              <Check
                                className={cn(
                                  "mr-2 h-4 w-4",
                                  field.value === inputValue
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
            </FormControl>
            <FormMessage />
          </FormItem>
        );
      }}
    />
  );
};
