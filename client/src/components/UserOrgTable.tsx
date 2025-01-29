import { DataTable } from "@/components/DataTable";
import { Button } from "@/components/ui/button";
import {
  Dialog,
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
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import {
  OrganizationInviteCreate,
  UserOrganizationPublic,
  UserPublic,
  UserRole,
} from "@/types/types";
import { useCreateOrganizationInviteMutation } from "@/utils/organizations";
import {
  useDeleteUserOrganizationMutation,
  userQueryOptions,
  usersByOrganizationQueryOptions,
} from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { PencilLine, Trash } from "lucide-react";
import { useRef } from "react";
import { useForm } from "react-hook-form";

export const UserOrgTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const { data: user } = useSuspenseQuery(userQueryOptions());
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
        return <EditUserPermissions user={row.original} />;
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
            <InviteUserButton />
            <RemoveUserDialog />
          </>
        )}
      />
    </>
  );
};

const InviteUserButton = () => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Invite user</Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <InviteUserForm />
      </DialogContent>
    </Dialog>
  );
};

const InviteUserForm = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const methods = useForm<OrganizationInviteCreate>({
    defaultValues: { email: "", invited_by: user.uuid },
  });
  const { toast } = useToast();
  const createOrganizationInvite = useCreateOrganizationInviteMutation();
  const organization = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  )?.organization;
  if (!organization) return null;
  const onSubmit = async (data: OrganizationInviteCreate) => {
    const created = await createOrganizationInvite.mutateAsync(data);
    if (created) {
      toast({
        title: "Successfully sent email invite",
      });
    } else {
      toast({
        title: "Failed to send email invite",
        variant: "destructive",
      });
    }
  };
  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className='space-y-6'>
        <DialogHeader className='flex-shrink-0'>
          <DialogTitle>{`Invite user to ${organization.name}`}</DialogTitle>
        </DialogHeader>
        <DialogDescription>
          An email will be sent to the user with an invitation to join the team.
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
        <DialogFooter>
          <Button
            type='submit'
            loading={methods.formState.isSubmitting}
            className='w-full'
          >
            {methods.formState.isSubmitting
              ? "Sending invite..."
              : "Send invite"}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  );
};

const EditUserPermissions = ({ user }: { user: UserPublic }) => {
  return (
    <div onClick={(e) => e.stopPropagation()}>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant='outline' size='icon' className='h-8 w-8'>
            <PencilLine />
          </Button>
        </DialogTrigger>
        <DialogContent className='max-w-[425px] overflow-x-auto'>
          <EditUserPermissionsForm editUser={user} />
        </DialogContent>
      </Dialog>
    </div>
  );
};

type EditUserPermissionsFormValues = {
  role: string;
};

const EditUserPermissionsForm = ({ editUser }: { editUser: UserPublic }) => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const userOrganization = editUser?.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  const methods = useForm<EditUserPermissionsFormValues>({
    defaultValues: { role: userOrganization?.role },
  });
  const onSubmit = async (data: EditUserPermissionsFormValues) => {};
  const roles = Object.values(UserRole);
  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className='space-y-6'>
        <DialogHeader className='flex-shrink-0'>
          <DialogTitle>{`Edit permissions for ${user.first_name}`}</DialogTitle>
        </DialogHeader>
        <DialogDescription>
          Update the user's role within the organization.
        </DialogDescription>
        <FormField
          key='role'
          control={methods.control}
          name='role'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Role</FormLabel>
              <FormControl>
                <Select value={field.value} onValueChange={field.onChange}>
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
          <Button
            type='submit'
            loading={methods.formState.isSubmitting}
            className='w-full'
          >
            {methods.formState.isSubmitting ? "Updating..." : "Update"}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  );
};

const RemoveUserDialog = ({
  deleteUser,
}: {
  deleteUser: UserOrganizationPublic;
}) => {
  const methods = useForm();
  const deleteUserOrganization = useDeleteUserOrganizationMutation();
  const { toast } = useToast();
  const onSubmit = async () => {
    const successfullyDeleted = await deleteUserOrganization.mutateAsync(
      deleteUser.uuid
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
              <DialogTitle>{`Remove`}</DialogTitle>
            </DialogHeader>
            <DialogDescription>{`Deleting ...`}</DialogDescription>
            <p className='text-red-500'>WARNING: This action is final.</p>
            <DialogFooter>
              <Button
                type='submit'
                variant='destructive'
                loading={methods.formState.isSubmitting}
                className='w-full'
              >
                {methods.formState.isSubmitting ? "Removing..." : "Remove user"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};
