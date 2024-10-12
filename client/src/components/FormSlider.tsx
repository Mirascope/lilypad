import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Control, Controller, FieldPath, FieldValues } from "react-hook-form";
import { SliderProps } from "@radix-ui/react-slider";
import { Input, InputProps } from "@/components/ui/input";
interface FormSliderProps<T extends FieldValues> {
  control: Control<T>;
  name: FieldPath<T>;
  label: string;
  sliderProps: SliderProps;
  showInput?: boolean;
  inputProps?: InputProps;
}
export const FormSlider = <T extends FieldValues>({
  control,
  name,
  label,
  showInput,
  sliderProps,
  inputProps,
}: FormSliderProps<T>) => {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div className='form-group flex flex-col gap-1.5'>
          <div className='flex justify-between items-center'>
            <Label htmlFor={sliderProps.name || ""}>{label}</Label>
            {showInput && <Input {...field} type='number' {...inputProps} />}
          </div>
          <Slider
            {...sliderProps}
            value={[field.value]}
            onValueChange={field.onChange}
          />
        </div>
      )}
    />
  );
};
