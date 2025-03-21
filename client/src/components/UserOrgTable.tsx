import { DataTable } from "@/components/DataTable";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Typography } from "@/components/ui/typography";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import {
  OrganizationInviteCreate,
  OrganizationInvitePublic,
  OrganizationPublic,
  UserOrganizationPublic,
  UserOrganizationUpdate,
  UserPublic,
  UserRole,
} from "@/types/types";
import { useCreateOrganizationInviteMutation } from "@/utils/organizations";
import {
  useDeleteUserOrganizationMutation,
  userQueryOptions,
  usersByOrganizationQueryOptions,
  useUpdateUserOrganizationMutation,
} from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { PencilLine, Trash } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";

export const UserOrgTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const features = useFeatureAccess();
  const userOrganization = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  if (!userOrganization) return null;
  const showCreateUser = features.users > data.length;
  const columns: ColumnDef<UserPublic>[] = [
    {
      accessorKey: "first_name",
      header: "Name",
    },
    {
      accessorKey: "email",
      header: "Email",
    },
    {
      id: "role",
      header: "Role",
      cell: ({ row }) => {
        const userOrganization = row.original.user_organizations?.find(
          (userOrg) =>
            userOrg.organization_uuid === user.active_organization_uuid
        );
        return <div>{userOrganization?.role}</div>;
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const rowUserOrganization = row.original.user_organizations?.find(
          (userOrg) =>
            userOrg.organization_uuid === user.active_organization_uuid
        ); // userOrganization is the user's role in the organization

        if (
          !rowUserOrganization ||
          rowUserOrganization.user_uuid === user.uuid ||
          userOrganization.role !== UserRole.OWNER
        )
          return null;
        return (
          <div className='flex gap-2'>
            <EditUserPermissionsDialog
              userOrganization={rowUserOrganization}
              user={row.original}
            />
            <RemoveUserDialog
              userOrganization={rowUserOrganization}
              user={row.original}
            />
          </div>
        );
      },
    },
  ];
  return (
    <>
      <Typography variant='h4'>Users</Typography>
      <DataTable<UserPublic>
        columns={columns}
        data={data}
        virtualizerRef={virtualizerRef}
        defaultPanelSize={50}
        virtualizerOptions={{
          count: data.length,
          estimateSize: () => 45,
          overscan: 5,
        }}
        hideColumnButton
        customControls={() => (
          <>
            {userOrganization.role !== UserRole.MEMBER && showCreateUser && (
              <InviteUserButton
                organization={userOrganization.organization}
                user={user}
              />
            )}
          </>
        )}
      />
    </>
  );
};

const InviteUserButton = ({
  organization,
  user,
}: {
  organization: OrganizationPublic;
  user: UserPublic;
}) => {
  const methods = useForm<OrganizationInviteCreate>({
    defaultValues: { email: "", invited_by: user.uuid },
  });
  const [organizationInvite, setOrganizationInvite] =
    useState<OrganizationInvitePublic | null>(null);
  const { toast } = useToast();
  const createOrganizationInvite = useCreateOrganizationInviteMutation();
  const onSubmit = async (data: OrganizationInviteCreate) => {
    const created = await createOrganizationInvite.mutateAsync(data);
    setOrganizationInvite(created);
    if (created.resend_email_id !== "n/a") {
      toast({
        title: "Successfully sent email invite.",
      });
    }
  };
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Invite user</Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <Form {...methods}>
          <form onSubmit={methods.handleSubmit(onSubmit)} className='space-y-6'>
            <DialogHeader className='flex-shrink-0'>
              <DialogTitle>{`Invite user to ${organization.name}`}</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              An email will be sent to the user with an invitation to join the
              team.
            </DialogDescription>
            <FormField
              key='email'
              control={methods.control}
              name='email'
              rules={{
                required: "Email is required",
                pattern: {
                  value: /\S+@\S+\.\S+/,
                  message: "Invalid email",
                },
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormDescription />
                </FormItem>
              )}
            />
            {organizationInvite && organizationInvite.invite_link && (
              <>
                <div>Alternatively, give the invited user this link:</div>
                <div className='flex items-center space-x-2'>
                  <Input value={organizationInvite.invite_link} readOnly />
                  <Button
                    type='button'
                    onClick={() => {
                      navigator.clipboard.writeText(
                        organizationInvite.invite_link || ""
                      );
                      toast({
                        title: "Copied link to clipboard",
                      });
                    }}
                  >
                    Copy
                  </Button>
                </div>
              </>
            )}
            <DialogFooter>
              {!organizationInvite ? (
                <Button
                  type='submit'
                  loading={methods.formState.isSubmitting}
                  className='w-full'
                >
                  {methods.formState.isSubmitting
                    ? "Sending invite..."
                    : "Send invite"}
                </Button>
              ) : (
                <DialogClose asChild>
                  <Button
                    variant='outline'
                    onClick={() => setOrganizationInvite(null)}
                    className='w-full'
                  >
                    Close
                  </Button>
                </DialogClose>
              )}
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

const EditUserPermissionsDialog = ({
  userOrganization,
  user,
}: {
  userOrganization: UserOrganizationPublic;
  user: UserPublic;
}) => {
  const updateUserOrganization = useUpdateUserOrganizationMutation();
  const { toast } = useToast();
  const methods = useForm<UserOrganizationUpdate>({
    defaultValues: { role: userOrganization?.role },
  });
  const onSubmit = async (data: UserOrganizationUpdate) => {
    const updated = await updateUserOrganization.mutateAsync({
      userOrganizationUuid: userOrganization.uuid,
      data,
    });
    if (updated) {
      toast({
        title: "Successfully updated user permissions",
      });
    } else {
      toast({
        title: "Failed to update user permissions",
        variant: "destructive",
      });
    }
  };
  const roles = Object.values(UserRole).filter(
    (role) => role !== UserRole.OWNER
  );
  return (
    <div onClick={(e) => e.stopPropagation()}>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant='outline' size='icon' className='h-8 w-8'>
            <PencilLine />
          </Button>
        </DialogTrigger>
        <DialogContent className='max-w-[425px] overflow-x-auto'>
          <Form {...methods}>
            <form
              onSubmit={methods.handleSubmit(onSubmit)}
              className='space-y-6'
            >
              <DialogHeader className='flex-shrink-0'>
                <DialogTitle>{`Edit permissions for ${user.first_name}`}</DialogTitle>
              </DialogHeader>
              <DialogDescription>
                Update <b>{user.first_name}'s</b> role within the organization.
              </DialogDescription>
              <FormField
                key='role'
                control={methods.control}
                name='role'
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <FormControl>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger className='w-full'>
                          <SelectValue placeholder='Change role' />
                        </SelectTrigger>
                        <SelectContent>
                          {roles.map((role) => (
                            <SelectItem key={role} value={role}>
                              {role}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter>
                <DialogClose asChild>
                  <Button
                    type='submit'
                    loading={methods.formState.isSubmitting}
                    className='w-full'
                  >
                    {methods.formState.isSubmitting ? "Updating..." : "Update"}
                  </Button>
                </DialogClose>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const RemoveUserDialog = ({
  userOrganization,
  user,
}: {
  userOrganization: UserOrganizationPublic;
  user: UserPublic;
}) => {
  const methods = useForm();
  const deleteUserOrganization = useDeleteUserOrganizationMutation();
  const { toast } = useToast();
  const onSubmit = async () => {
    const successfullyDeleted = await deleteUserOrganization.mutateAsync(
      userOrganization.uuid
    );
    let title = "Failed to remove user. Please try again.";
    if (successfullyDeleted) {
      title = "Successfully removed user.";
    }
    toast({
      title,
    });
  };

  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        <Button variant='outlineDestructive' size='icon' className='h-8 w-8'>
          <Trash />
        </Button>
      </DialogTrigger>
      <DialogContent
        className={"max-w-[425px] overflow-x-auto"}
        onClick={(e) => e.stopPropagation()}
      >
        <Form {...methods}>
          <form onSubmit={methods.handleSubmit(onSubmit)} className='space-y-6'>
            <DialogHeader className='flex-shrink-0'>
              <DialogTitle>{`Remove ${user.first_name}`}</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              This action will remove <b>{user.first_name}</b> from{" "}
              <b>{userOrganization.organization.name}</b>
            </DialogDescription>
            <DialogFooter>
              <DialogClose asChild>
                <Button
                  type='submit'
                  variant='destructive'
                  loading={methods.formState.isSubmitting}
                  className='w-full'
                >
                  {methods.formState.isSubmitting
                    ? "Removing..."
                    : "Remove user"}
                </Button>
              </DialogClose>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};
