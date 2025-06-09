import { FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/src/components/ui/form";
import { Input, InputProps } from "@/src/components/ui/input";
import { Label } from "@/src/components/ui/label";
import { Slider } from "@/src/components/ui/slider";
import { Switch } from "@/src/components/ui/switch";
import { SliderProps } from "@radix-ui/react-slider";
import { Controller, FieldValues, Path, useFormContext } from "react-hook-form";

interface FormSliderProps<T extends FieldValues> {
  name: Path<T>;
  label: string;
  optional?: boolean;
  switchName?: Path<T>;
  sliderProps: Omit<SliderProps, "value" | "onChange">;
  showInput?: boolean;
  inputProps?: Omit<InputProps, "value" | "onChange">;
  isDisabled?: boolean;
}

export const FormSlider = <T extends FieldValues>({
  name,
  switchName,
  label,
  optional,
  showInput,
  sliderProps,
  inputProps,
  isDisabled: isDisabledProp,
}: FormSliderProps<T>) => {
  const { control, watch } = useFormContext<T>();
  return (
    <FormField
      name={name}
      control={control}
      render={({ field }) => {
        const isDisabled = (switchName && !watch(switchName)) ?? isDisabledProp;

        return (
          <FormItem>
            <FormLabel className="flex items-center justify-between">
              <Label htmlFor={sliderProps.name ?? ""} className="flex items-center gap-2">
                {label}
                {optional && switchName && (
                  <>
                    <Controller
                      name={switchName}
                      control={control}
                      render={({ field: switchField }) => (
                        <>
                          <Switch
                            checked={switchField.value}
                            onCheckedChange={switchField.onChange}
                          />
                          <p className="text-xs">{switchField.value ? "Active" : "Not set"}</p>
                        </>
                      )}
                    />
                  </>
                )}
              </Label>
              {showInput && (
                <Input
                  {...inputProps}
                  value={field.value}
                  onChange={(e) => {
                    // Convert to number for the field
                    const val = e.target.value === "" ? "" : Number(e.target.value);
                    field.onChange(val);
                  }}
                  type="number"
                  disabled={isDisabled}
                />
              )}
            </FormLabel>
            <FormControl>
              <Slider
                {...sliderProps}
                value={[Number(field.value) || 0]} // Ensure it's a number and defaults to 0 if undefined
                onValueChange={(values) => field.onChange(values[0])}
                disabled={isDisabled}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        );
      }}
    />
  );
};
