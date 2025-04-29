import {
  BaseProjectForm,
  ProjectFormData,
} from "@/components/projects/BaseProjectForm";
import { useUpdateProjectMutation } from "@/utils/projects";
import { toast } from "sonner";

interface EditProjectFormProps {
  projectUuid: string;
  defaultProjectFormData: ProjectFormData;
  onSuccess?: () => void;
  className?: string;
}

export const EditProjectForm = ({
  projectUuid,
  defaultProjectFormData,
  onSuccess,
  className,
}: EditProjectFormProps) => {
  const updateProject = useUpdateProjectMutation();

  const handleEdit = async (data: ProjectFormData) => {
    await updateProject
      .mutateAsync({
        projectUuid,
        projectUpdate: data,
      })
      .then(() => {
        toast.success("Successfully updated project");
        onSuccess?.();
      })
      .catch(() => {
        toast.error("Failed to update project");
      });
  };

  return (
    <BaseProjectForm
      defaultValues={defaultProjectFormData}
      onSubmit={handleEdit}
      submitButtonText='Save Changes'
      submittingText='Saving...'
      className={className}
    />
  );
};
