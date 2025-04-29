import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ProjectPublic } from "@/types/types";
import { useDeleteProjectMutation } from "@/utils/projects";
import { useNavigate } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

interface BaseDeleteProjectFormProps {
  project: ProjectPublic;
  onSubmit: () => Promise<void>;
  className?: string;
}

export const BaseDeleteProjectForm = ({
  project,
  onSubmit,
  className = "",
}: BaseDeleteProjectFormProps) => {
  const methods = useForm<{ projectName: string }>({
    defaultValues: {
      projectName: "",
    },
  });

  const handleSubmit = async () => {
    await onSubmit();
    methods.reset();
  };

  return (
    <Form {...methods}>
      <form
        onSubmit={methods.handleSubmit(handleSubmit)}
        className={`space-y-6 ${className}`}
      >
        <p className='text-red-500'>WARNING: This action is final.</p>
        <FormField
          key='projectName'
          control={methods.control}
          name='projectName'
          rules={{
            required: "Project name is required",
            validate: (value) =>
              value === project.name || "Project name doesn't match",
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormDescription>
                Please type &quot;{project.name}&quot; to confirm deletion
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className='flex justify-end'>
          <Button
            type='submit'
            variant='destructive'
            disabled={methods.formState.isSubmitting}
          >
            {methods.formState.isSubmitting ? "Deleting..." : "Delete Project"}
          </Button>
        </div>
      </form>
    </Form>
  );
};

interface DeleteProjectFormProps {
  project: ProjectPublic;
  onSuccess?: () => void;
  className?: string;
}

export const DeleteProjectForm = ({
  project,
  onSuccess,
  className,
}: DeleteProjectFormProps) => {
  const deleteProject = useDeleteProjectMutation();
  const navigate = useNavigate();

  const handleDelete = async () => {
    await deleteProject
      .mutateAsync(project.uuid)
      .then(() => {
        toast.success("Successfully deleted project");
        navigate({
          to: "/projects",
        }).catch(() => toast.error("Failed to navigate after deletion."));
        onSuccess?.();
      })
      .catch(() => {
        toast.error("Failed to delete project. Please try again.");
      });
  };

  return (
    <BaseDeleteProjectForm
      project={project}
      onSubmit={handleDelete}
      className={className}
    />
  );
};
