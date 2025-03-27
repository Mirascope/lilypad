import { Combobox, MultipleComboboxProps } from "@/components/ui/combobox";
import { FormField } from "@/components/ui/form";
import { Control, FieldValues, Path } from "react-hook-form";

type FormComboboxProps<T extends FieldValues> = Omit<
  MultipleComboboxProps,
  "value" | "onChange" | "multiple"
> & {
  name: Path<T>;
  control: Control<T>;
};

export const FormCombobox = <T extends FieldValues>({
  items,
  name,
  control,
  popoverText = "Select items...",
  helperText = "Search item...",
  emptyText = "No item found.",
  disabled,
  disableAdd,
}: FormComboboxProps<T>) => {
  return (
    <FormField
      name={name}
      control={control}
      render={({ field }) => (
        <Combobox
          items={items}
          value={field.value || []}
          onChange={field.onChange}
          popoverText={popoverText}
          helperText={helperText}
          emptyText={emptyText}
          disabled={disabled}
          disableAdd={disableAdd}
          multiple={true}
        />
      )}
    />
  );
};
