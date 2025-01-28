import { FailButton } from "@/components/FailButton";
import { SuccessButton } from "@/components/SuccessButton";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { useForm } from "react-hook-form";

type AnnotationFormValues = {
  label: string;
  reasoning: string;
};
export const AnnotationForm = () => {
  const methods = useForm<AnnotationFormValues>({
    defaultValues: {
      label: "",
      reasoning: "",
    },
  });
  const onSubmit = (data: AnnotationFormValues) => {
    console.log(data);
  };
  return (
    <Form {...methods}>
      <form
        className='flex flex-col gap-2'
        onSubmit={methods.handleSubmit(onSubmit)}
      >
        <FormField
          key='label'
          control={methods.control}
          name='label'
          rules={{ required: "Label is required" }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Label</FormLabel>
              <FormControl>
                <div className='flex gap-4'>
                  <SuccessButton
                    onClick={() => field.onChange("success")}
                    variant={field.value === "success" ? "success" : "outline"}
                  >
                    Pass
                  </SuccessButton>
                  <FailButton
                    onClick={() => field.onChange("fail")}
                    variant={field.value === "fail" ? "destructive" : "outline"}
                  >
                    Fail
                  </FailButton>
                </div>
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          key='reasoning'
          control={methods.control}
          name='reasoning'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Reason</FormLabel>
              <FormControl>
                <Textarea
                  placeholder='(Optional) Reason for label '
                  {...field}
                />
              </FormControl>
            </FormItem>
          )}
        />
        <Button
          type='submit'
          loading={methods.formState.isSubmitting}
          className='w-full'
        >
          {methods.formState.isSubmitting ? "Staging..." : "Annotate"}
        </Button>
      </form>
    </Form>
  );
};
