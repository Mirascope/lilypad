import { FailButton } from "@/components/FailButton";
import { SuccessButton } from "@/components/SuccessButton";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { usersByOrganizationQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

type AnnotationFormValues = {
  label: string;
  reasoning: string;
  assignedTo?: string;
};
export const AnnotationForm = () => {
  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
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
        <FormField
          key='assignedTo'
          control={methods.control}
          name='assignedTo'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Assign To</FormLabel>
              <FormDescription>
                Leave empty to allow anyone to annotate
              </FormDescription>
              <FormControl>
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger className='w-full'>
                    <SelectValue placeholder='Assign user' />
                  </SelectTrigger>
                  <SelectContent>
                    {users.map((user) => (
                      <SelectItem key={user.uuid} value={user.uuid}>
                        {user.first_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
