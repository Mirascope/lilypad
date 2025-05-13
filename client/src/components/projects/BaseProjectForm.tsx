import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useForm } from "react-hook-form";

export interface ProjectFormData {
  name: string;
}

// #1 - Base Project Form Component
interface BaseProjectFormProps {
  defaultValues: ProjectFormData;
  onSubmit: (data: ProjectFormData) => Promise<void>;
  submitButtonText: string;
  submittingText: string;
  className?: string;
}

export const BaseProjectForm = ({
  defaultValues,
  onSubmit,
  submitButtonText,
  submittingText,
  className = "",
}: BaseProjectFormProps) => {
  const methods = useForm<ProjectFormData>({
    defaultValues,
  });

  const handleSubmit = async (data: ProjectFormData) => {
    await onSubmit(data);
    methods.reset();
  };

  return (
    <Form {...methods}>
      <form
        onSubmit={methods.handleSubmit(handleSubmit)}
        className={`space-y-6 ${className}`}
      >
        <FormField
          control={methods.control}
          name='name'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />

        <div className='flex justify-end'>
          <Button type='submit' disabled={methods.formState.isSubmitting}>
            {methods.formState.isSubmitting ? submittingText : submitButtonText}
          </Button>
        </div>
      </form>
    </Form>
  );
};
