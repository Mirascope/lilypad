import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { EnvironmentCreate } from "@/types/types";
import { useCreateEnvironmentMutation } from "@/utils/environments";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

interface CreateEnvironmentFormProps {
  customButtons?: React.ReactNode;
}
export const CreateEnvironmentForm = ({ customButtons }: CreateEnvironmentFormProps) => {
  const methods = useForm<EnvironmentCreate>({
    defaultValues: { name: "", description: "", is_default: false },
  });
  const createEnvironment = useCreateEnvironmentMutation();

  const onSubmit = async (data: EnvironmentCreate) => {
    await createEnvironment
      .mutateAsync(data)
      .catch(() => toast.error("Failed to create environment"));
    toast.success("Successfully created environment");
    methods.reset();
  };

  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          key="name"
          control={methods.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Environment Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          key="description"
          control={methods.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea {...field} value={field.value ?? ""} />
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          key="is_default"
          control={methods.control}
          name="is_default"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <FormLabel>Default Environment</FormLabel>
                <FormDescription>Set as default environment for new API keys</FormDescription>
              </div>
              <FormControl>
                <Switch checked={field.value} onCheckedChange={field.onChange} />
              </FormControl>
            </FormItem>
          )}
        />
        {customButtons ?? (
          <div className="flex justify-end">
            <Button type="submit" loading={methods.formState.isSubmitting}>
              {methods.formState.isSubmitting ? "Creating..." : "Create Environment"}
            </Button>
          </div>
        )}
      </form>
    </Form>
  );
};
