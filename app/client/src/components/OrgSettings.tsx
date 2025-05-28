import { useAuth } from "@/auth";
import { APIKeysTable } from "@/components/apiKeys/APIKeysTable";
import { EnvironmentsTable } from "@/components/environments/EnvironmentsTable";
import LilypadDialog from "@/components/LilypadDialog";
import { NotFound } from "@/components/NotFound";
import { UpdateOrganizationDialog } from "@/components/OrganizationDialog";
import { PlanList } from "@/components/PlanList.tsx";
import { ProjectsTable } from "@/components/projects/ProjectsTable";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
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
import { Typography } from "@/components/ui/typography";
import { UserTable } from "@/components/users/UserTable";
import { UserRole } from "@/types/types";
import { useDeleteOrganizationMutation } from "@/utils/organizations";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Pencil, Trash, TriangleAlert } from "lucide-react";
import { Dispatch, SetStateAction, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

interface OrgSettingsProps {
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
}
export const OrgSettings = ({ open, setOpen }: OrgSettingsProps) => {
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const activeUserOrg = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  if (!activeUserOrg) return <NotFound />;
  return (
    <div className="flex flex-col gap-2">
      <div
        className="flex cursor-pointer items-center gap-2"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <Typography variant="h3">{activeUserOrg?.organization.name}&apos;s Settings</Typography>
        {isHovered && <Pencil className="size-4 text-gray-500" onClick={() => setOpen(true)} />}
      </div>
      <PlanList />
      <UpdateOrganizationDialog open={open} setOpen={setOpen} />
      <UserTable />
      <ProjectsTable />
      <EnvironmentsTable />
      <APIKeysTable />
      {activeUserOrg.role === UserRole.OWNER && (
        <Alert variant="destructive" className="mt-8">
          <TriangleAlert className="h-4 w-4" />
          <div className="flex flex-col gap-2">
            <AlertTitle>Danger Zone</AlertTitle>
            <AlertDescription>This action is permanent.</AlertDescription>
            <div className="mt-2">
              <DeleteOrganizationButton name={activeUserOrg.organization.name} />
            </div>
          </div>
        </Alert>
      )}
    </div>
  );
};

interface DeleteOrganizationFormValues {
  organizationName: string;
}
const DeleteOrganizationButton = ({ name }: { name: string }) => {
  const methods = useForm<DeleteOrganizationFormValues>({
    defaultValues: {
      organizationName: "",
    },
  });
  const auth = useAuth();
  const deleteOrganizationMutation = useDeleteOrganizationMutation();
  const navigate = useNavigate();
  const handleSubmit = async () => {
    const newSession = await deleteOrganizationMutation.mutateAsync().catch(() => {
      toast.error("Failed to delete organization. Please try again.");
      return null;
    });
    toast.success("Successfully deleted organization");
    auth.setSession(newSession);
    navigate({
      to: "/projects",
    }).catch(() => toast.error("Failed to navigate after deletion."));
  };
  return (
    <LilypadDialog
      customTrigger={
        <Button variant="destructive">
          <Trash className="mr-2 h-4 w-4" /> Delete Organization
        </Button>
      }
      title={`Delete ${name}`}
      description={`Deleting ${name} will delete all resources tied to this organization.`}
    >
      <Form {...methods}>
        <form onSubmit={methods.handleSubmit(handleSubmit)} className="space-y-6">
          <Alert variant="destructive">
            <TriangleAlert className="h-4 w-4" />
            <div className="flex flex-col gap-2">
              <AlertTitle>WARNING</AlertTitle>
              <AlertDescription>This action is final.</AlertDescription>
            </div>
          </Alert>
          <FormField
            key="organizationName"
            control={methods.control}
            name="organizationName"
            rules={{
              required: "Organization name is required",
              validate: (value) => value === name || "Organization name doesn't match",
            }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Organization Name</FormLabel>
                <FormDescription>
                  Please type &quot;{name}&quot; to confirm deletion
                </FormDescription>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <DialogFooter>
            <Button
              key="submit"
              type="submit"
              variant="outlineDestructive"
              disabled={methods.formState.isSubmitting}
              className="w-full"
            >
              {methods.formState.isSubmitting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </form>
      </Form>
    </LilypadDialog>
  );
};
