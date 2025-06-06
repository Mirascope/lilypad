import { useAuth } from "@/src/auth";
import LilypadDialog from "@/src/components/LilypadDialog";
import { Button } from "@/src/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel } from "@/src/components/ui/form";
import { Input } from "@/src/components/ui/input";
import {
  useCreateOrganizationMutation,
  useUpdateOrganizationMutation,
} from "@/src/utils/organizations";
import { useUpdateActiveOrganizationMutation } from "@/src/utils/users";
import { Dispatch, ReactNode, SetStateAction } from "react";
import { DefaultValues, Path, useForm } from "react-hook-form";
import { toast } from "sonner";

interface FormData {
  name: string;
}

interface OrganizationFormProps<T extends FormData> {
  defaultValues: T;
  onSubmit: (data: T) => Promise<void>;
  submitButtonText: string;
  submitButtonLoadingText: string;
  className?: string;
}

export const OrganizationForm = <T extends FormData>({
  defaultValues,
  onSubmit,
  submitButtonText,
  submitButtonLoadingText,
  className = "",
}: OrganizationFormProps<T>) => {
  const methods = useForm<T>({
    defaultValues: defaultValues as DefaultValues<T>,
  });
  const name = methods.watch("name" as Path<T>);

  const handleSubmit = async () => {
    const data = { ...defaultValues, name } as T;
    await onSubmit(data);
    methods.reset();
  };

  return (
    <Form {...methods}>
      <form className={`space-y-6 ${className}`} onSubmit={methods.handleSubmit(handleSubmit)}>
        <FormField
          control={methods.control}
          name={"name" as Path<T>}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Organization Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <div className="flex justify-end">
          <Button key="submit" type="submit" disabled={methods.formState.isSubmitting}>
            {methods.formState.isSubmitting ? submitButtonLoadingText : submitButtonText}
          </Button>
        </div>
      </form>
    </Form>
  );
};

interface CreateOrganizationFormProps {
  onSuccess?: () => void;
  className?: string;
}

export const CreateOrganizationForm = ({ onSuccess, className }: CreateOrganizationFormProps) => {
  const auth = useAuth();
  const organizationCreateMutation = useCreateOrganizationMutation();
  const updateActiveOrganizationMutation = useUpdateActiveOrganizationMutation();

  const handleCreateSubmit = async (data: { name: string }) => {
    const newOrganization = await organizationCreateMutation
      .mutateAsync({
        name: data.name,
      })
      .catch(() => {
        toast.error("Failed to create organization");
        return null;
      });

    if (!newOrganization) return;

    toast.success("Organization created");

    const newSession = await updateActiveOrganizationMutation.mutateAsync({
      organizationUuid: newOrganization.uuid,
    });

    auth.setSession(newSession);
    onSuccess?.();
  };

  return (
    <OrganizationForm
      defaultValues={{ name: "" }}
      onSubmit={handleCreateSubmit}
      submitButtonText="Create"
      submitButtonLoadingText="Creating..."
      className={className}
    />
  );
};

interface UpdateOrganizationFormProps {
  initialName?: string;
  onSuccess?: () => void;
  className?: string;
}

export const UpdateOrganizationForm = ({
  initialName = "",
  onSuccess,
  className,
}: UpdateOrganizationFormProps) => {
  const updateOrganizationMutation = useUpdateOrganizationMutation();

  const handleUpdateSubmit = async (data: { name: string }) => {
    await updateOrganizationMutation
      .mutateAsync({
        name: data.name,
      })
      .then(() => {
        toast.success("Organization updated");
        onSuccess?.();
      })
      .catch(() => {
        toast.error("Failed to update organization");
      });
  };

  return (
    <OrganizationForm
      defaultValues={{ name: initialName }}
      onSubmit={handleUpdateSubmit}
      submitButtonText="Update"
      submitButtonLoadingText="Updating..."
      className={className}
    />
  );
};

interface BaseDialogProps {
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
  title: string;
  description: string;
  children: ReactNode;
}

export const BaseOrganizationDialog = ({
  open,
  setOpen,
  title,
  description,
  children,
}: BaseDialogProps) => {
  return (
    <LilypadDialog
      open={open}
      onOpenChange={setOpen}
      noTrigger
      title={title}
      description={description}
    >
      {children}
    </LilypadDialog>
  );
};

interface CreateOrganizationDialogProps {
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
}

export const CreateOrganizationDialog = ({ open, setOpen }: CreateOrganizationDialogProps) => {
  return (
    <BaseOrganizationDialog
      open={open}
      setOpen={setOpen}
      title="New Organization"
      description="Create a new organization"
    >
      <CreateOrganizationForm onSuccess={() => setOpen(false)} />
    </BaseOrganizationDialog>
  );
};

interface UpdateOrganizationDialogProps {
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
  initialName?: string;
}

export const UpdateOrganizationDialog = ({
  open,
  setOpen,
  initialName = "",
}: UpdateOrganizationDialogProps) => {
  return (
    <BaseOrganizationDialog
      open={open}
      setOpen={setOpen}
      title="Update Organization"
      description="Update organization details"
    >
      <UpdateOrganizationForm initialName={initialName} onSuccess={() => setOpen(false)} />
    </BaseOrganizationDialog>
  );
};
