import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Control, Controller, FieldPath, FieldValues } from "react-hook-form";
import { SliderProps } from "@radix-ui/react-slider";
import { Input, InputProps } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useState } from "react";

interface FormSliderProps<T extends FieldValues> {
  control: Control<T>;
  name: FieldPath<T>;
  label: string;
  optional?: boolean;
  sliderProps: SliderProps;
  showInput?: boolean;
  inputProps?: InputProps;
}
export const FormSlider = <T extends FieldValues>({
  control,
  name,
  label,
  optional,
  showInput,
  sliderProps,
  inputProps,
}: FormSliderProps<T>) => {
  const [disabled, setDisabled] = useState<boolean>(false);
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div className='form-group flex flex-col gap-1.5'>
          <div className='flex justify-between items-center'>
            <Label
              htmlFor={sliderProps.name || ""}
              className='flex items-center gap-2'
            >
              {label}
              {optional && (
                <>
                  <Switch
                    checked={disabled}
                    onCheckedChange={() =>
                      setDisabled((prevDisabled) => !prevDisabled)
                    }
                  />
                  <p className='text-xs'>{"Use Default"}</p>
                </>
              )}
            </Label>
            {showInput && (
              <Input
                {...field}
                {...inputProps}
                type='number'
                disabled={disabled}
              />
            )}
          </div>
          <Slider
            {...sliderProps}
            value={[field.value]}
            onValueChange={field.onChange}
            disabled={disabled}
          />
        </div>
      )}
    />
  );
};
