import { BaseProjectForm, ProjectFormData } from "@/src/components/projects/BaseProjectForm";
import { useCreateProjectMutation } from "@/src/utils/projects";
import { toast } from "sonner";
interface CreateProjectFormProps {
  onSuccess?: () => void;
  className?: string;
}

export const CreateProjectForm = ({ onSuccess, className }: CreateProjectFormProps) => {
  const createProject = useCreateProjectMutation();

  const handleCreate = async (data: ProjectFormData) => {
    await createProject
      .mutateAsync(data)
      .then(() => {
        toast.success("Successfully created project");
        onSuccess?.();
      })
      .catch(() => {
        toast.error("Failed to create project");
      });
  };

  return (
    <BaseProjectForm
      defaultValues={{ name: "" }}
      onSubmit={handleCreate}
      submitButtonText="Create Project"
      submittingText="Creating..."
      className={className}
    />
  );
};
