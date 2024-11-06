import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Control,
  Controller,
  Path,
  FieldValues,
  useWatch,
} from "react-hook-form";
import { SliderProps } from "@radix-ui/react-slider";
import { Input, InputProps } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

type FormSliderProps<T extends FieldValues> = {
  control: Control<T>;
  name: Path<T>;
  label: string;
  optional?: boolean;
  switchName?: Path<T>;
  sliderProps: Omit<SliderProps, "value" | "onChange">;
  showInput?: boolean;
  inputProps?: Omit<InputProps, "value" | "onChange">;
};

export const FormSlider = <T extends FieldValues>({
  control,
  name,
  switchName,
  label,
  optional,
  showInput,
  sliderProps,
  inputProps,
}: FormSliderProps<T>) => {
  const switchValue = useWatch({
    control,
    name: switchName || name,
    disabled: !switchName,
  });
  const disabled = optional && switchName ? !switchValue : false;
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div className='form-group'>
          <div className='flex justify-between items-center'>
            <Label
              htmlFor={sliderProps.name || ""}
              className='flex items-center gap-2'
            >
              {label}
              {optional && switchName && (
                <>
                  <Controller
                    name={switchName}
                    control={control}
                    render={({ field }) => (
                      <>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                        <p className='text-xs'>
                          {field.value ? "Active" : "Not set"}
                        </p>
                      </>
                    )}
                  />
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
