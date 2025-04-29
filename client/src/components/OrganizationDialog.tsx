import { useAuth } from "@/auth";
import LilypadDialog from "@/components/LilypadDialog";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  useCreateOrganizationMutation,
  useUpdateOrganizationMutation,
} from "@/utils/organizations";
import { useUpdateActiveOrganizationMutation } from "@/utils/users";
import { Dispatch, SetStateAction } from "react";
import { DefaultValues, Path, useForm } from "react-hook-form";
import { toast } from "sonner";

// Base props for organization dialogs
interface BaseOrganizationDialogProps {
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
}

// Form data interface with generic extension capability
interface FormData {
  name: string;
}

// Base component for organization dialogs
function BaseOrganizationDialog<T extends FormData>({
  open,
  setOpen,
  title,
  description,
  defaultValues,
  onSubmit,
  submitButtonText,
  submitButtonLoadingText,
}: BaseOrganizationDialogProps & {
  title: string;
  description: string;
  defaultValues: T;
  onSubmit: (data: T) => Promise<void>;
  submitButtonText: string;
  submitButtonLoadingText: string;
}) {
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
    <LilypadDialog
      open={open}
      onOpenChange={setOpen}
      noTrigger
      title={title}
      description={description}
    >
      <Form {...methods}>
        <form
          className="space-y-6"
          onSubmit={methods.handleSubmit(handleSubmit)}
        >
          <FormField
            control={methods.control}
            name={"name" as Path<T>}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
              </FormItem>
            )}
          />
          <DialogFooter>
            <Button
              key="submit"
              type="submit"
              disabled={methods.formState.isSubmitting}
              className="w-full"
            >
              {methods.formState.isSubmitting
                ? submitButtonLoadingText
                : submitButtonText}
            </Button>
          </DialogFooter>
        </form>
      </Form>
    </LilypadDialog>
  );
}

// Create Organization Dialog
type CreateOrganizationDialogProps = BaseOrganizationDialogProps;

export const CreateOrganizationDialog = ({
  open,
  setOpen,
}: CreateOrganizationDialogProps) => {
  const auth = useAuth();
  const organizationCreateMutation = useCreateOrganizationMutation();
  const updateActiveOrganizationMutation =
    useUpdateActiveOrganizationMutation();

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
    setOpen(false);
  };

  return (
    <BaseOrganizationDialog
      open={open}
      setOpen={setOpen}
      title="New Organization"
      description="Create a new organization"
      defaultValues={{ name: "" }}
      onSubmit={handleCreateSubmit}
      submitButtonText="Create"
      submitButtonLoadingText="Creating..."
    />
  );
};

// Update Organization Dialog
type UpdateOrganizationDialogProps = BaseOrganizationDialogProps;
export const UpdateOrganizationDialog = ({
  open,
  setOpen,
}: UpdateOrganizationDialogProps) => {
  const updateOrganizationMutation = useUpdateOrganizationMutation();

  const handleUpdateSubmit = async (data: { name: string }) => {
    await updateOrganizationMutation
      .mutateAsync({
        name: data.name,
      })
      .then(() => {
        toast.success("Organization updated");
        setOpen(false);
      })
      .catch(() => {
        toast.error("Failed to update organization");
      });
  };

  return (
    <BaseOrganizationDialog
      open={open}
      setOpen={setOpen}
      title="Update Organization"
      description="Update organization details"
      defaultValues={{ name: "" }}
      onSubmit={handleUpdateSubmit}
      submitButtonText="Update"
      submitButtonLoadingText="Updating..."
    />
  );
};
