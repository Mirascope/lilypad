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
import { usersByOrganizationQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";

type QueueFormValues = {
  assignedTo?: string;
};
export const QueueForm = () => {
  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const methods = useForm<QueueFormValues>();
  const onSubmit = (data: QueueFormValues) => {
    console.log(data);
  };
  return (
    <Form {...methods}>
      <form
        className='flex flex-col gap-2'
        onSubmit={methods.handleSubmit(onSubmit)}
      >
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
          {methods.formState.isSubmitting
            ? "Adding to queue..."
            : "Add to queue"}
        </Button>
      </form>
    </Form>
  );
};
