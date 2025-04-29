import { DataTable } from "@/components/DataTable";
import LilypadDialog from "@/components/LilypadDialog";
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
import {
  organizationInvitesQueryOptions,
  useCreateOrganizationInviteMutation,
  useDeleteOrganizationInviteMutation,
} from "@/utils/organizations";
import {
  useDeleteUserOrganizationMutation,
  userQueryOptions,
  usersByOrganizationQueryOptions,
  useUpdateUserOrganizationMutation,
} from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { Copy, Mail, PencilLine, PlusCircle, Trash } from "lucide-react";
import { Dispatch, SetStateAction, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

type UserData = UserPublic | ({ isInvite: true } & OrganizationInvitePublic);

export const UserOrgTable = () => {
  const virtualizerRef = useRef<HTMLDivElement>(null);
  const { data: users } = useSuspenseQuery(usersByOrganizationQueryOptions());
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const { data: invitedUsers } = useSuspenseQuery(
    organizationInvitesQueryOptions()
  );
  const [activeInvite, setActiveInvite] = useState<
    (OrganizationInvitePublic & { isInvite: true }) | null
  >(null);
  const [resendInviteOpen, setResendInviteOpen] = useState<boolean>(false);

  const features = useFeatureAccess();
  const userOrganization = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );

  if (!userOrganization) return null;

  const combinedData: UserData[] = [
    ...users,
    ...invitedUsers.map((invite) => ({ ...invite, isInvite: true as const })),
  ];

  const showCreateUser = features.users > users.length;

  const handleOpenResendDialog = (
    invite: OrganizationInvitePublic & { isInvite: true }
  ) => {
    setActiveInvite(invite);
    setResendInviteOpen(true);
  };

  const columns: ColumnDef<UserData>[] = [
    {
      accessorKey: "first_name",
      header: "Name",
      cell: ({ row }) => {
        const rowData = row.original;
        if ("isInvite" in rowData) {
          return <i>Pending Invite</i>;
        }
        return <div>{rowData.first_name}</div>;
      },
    },
    {
      accessorKey: "email",
      header: "Email",
      cell: ({ row }) => {
        const rowData = row.original;
        if ("isInvite" in rowData) {
          return <div>{rowData.email}</div>;
        }
        return <div>{rowData.email}</div>;
      },
    },
    {
      id: "role",
      header: "Role",
      cell: ({ row }) => {
        const rowData = row.original;
        if ("isInvite" in rowData) {
          return <div>Invited</div>;
        }

        const userOrganization = rowData.user_organizations?.find(
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
        const rowData = row.original;

        // For invited users
        if ("isInvite" in rowData) {
          if (
            userOrganization.role !== UserRole.OWNER &&
            userOrganization.role !== UserRole.ADMIN
          ) {
            return null;
          }

          return (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={(e) => {
                  e.stopPropagation();
                  handleOpenResendDialog(rowData);
                }}
              >
                <Mail size={16} />
              </Button>
              <CancelInviteButton invite={rowData} />
            </div>
          );
        }

        // For regular users
        const rowUserOrganization = rowData.user_organizations?.find(
          (userOrg) =>
            userOrg.organization_uuid === user.active_organization_uuid
        );

        if (
          !rowUserOrganization ||
          rowUserOrganization.user_uuid === user.uuid ||
          userOrganization.role !== UserRole.OWNER
        )
          return null;

        return (
          <div className="flex gap-2">
            <EditUserPermissionsDialog
              userOrganization={rowUserOrganization}
              user={rowData}
            />
            <RemoveUserDialog
              userOrganization={rowUserOrganization}
              user={rowData}
            />
          </div>
        );
      },
    },
  ];

  return (
    <>
      <div className="flex gap-2 items-center">
        <Typography variant="h4">Users</Typography>
        {userOrganization.role !== UserRole.MEMBER && showCreateUser && (
          <InviteUserButton
            organization={userOrganization.organization}
            user={user}
          />
        )}
      </div>
      <DataTable
        columns={columns}
        data={combinedData}
        virtualizerRef={virtualizerRef}
        defaultPanelSize={50}
        virtualizerOptions={{
          count: combinedData.length,
          estimateSize: () => 45,
          overscan: 5,
        }}
        hideColumnButton
      />
      {activeInvite && (
        <ResendInviteDialog
          invite={activeInvite}
          open={resendInviteOpen}
          setOpen={setResendInviteOpen}
          onClose={() => setActiveInvite(null)}
        />
      )}
    </>
  );
};

const ResendInviteDialog = ({
  invite,
  open,
  setOpen,
  onClose,
}: {
  invite: OrganizationInvitePublic & { isInvite: true };
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
  onClose: () => void;
}) => {
  const resendInvite = useCreateOrganizationInviteMutation();
  const [newOrganizationInvite, setNewOrganizationInvite] =
    useState<OrganizationInvitePublic | null>(null);

  const handleClose = () => {
    setOpen(false);
    setNewOrganizationInvite(null);
    onClose();
  };

  const handleResend = async () => {
    const result = await resendInvite
      .mutateAsync({
        email: invite.email,
        organization_uuid: invite.organization_uuid,
        invited_by: invite.invited_by,
      })
      .catch(() => {
        toast.error("Failed to resend invitation");
        return null;
      });
    if (!result) {
      return;
    }
    setNewOrganizationInvite(result);
    toast.success(`Invitation successfully resent to ${invite.email}.`);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(newOpen) => {
        if (!newOpen) {
          handleClose();
        } else {
          setOpen(true);
        }
      }}
    >
      <DialogContent onClick={(e) => e.stopPropagation()}>
        <DialogHeader>
          <DialogTitle>Resend invitation</DialogTitle>
          <DialogDescription>
            {!newOrganizationInvite
              ? `Are you sure you want to resend the invitation to ${invite.email}?`
              : `Invitation successfully resent to ${invite.email}.`}
          </DialogDescription>
        </DialogHeader>

        {newOrganizationInvite?.invite_link && (
          <AlternativeInviteLink
            inviteLink={newOrganizationInvite.invite_link}
          />
        )}

        <DialogFooter>
          {!newOrganizationInvite ? (
            <Button
              loading={resendInvite.isPending}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                handleResend();
              }}
            >
              Resend invitation
            </Button>
          ) : (
            <Button onClick={handleClose}>Close</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

const CancelInviteButton = ({
  invite,
}: {
  invite: OrganizationInvitePublic & { isInvite: true };
}) => {
  const deleteInvite = useDeleteOrganizationInviteMutation();

  const handleDelete = () => {
    deleteInvite
      .mutateAsync(invite.uuid)
      .then(() => {
        toast.success("Invitation cancelled successfully");
      })
      .catch(() => {
        toast.error("Failed to cancel invitation");
      });
  };

  return (
    <LilypadDialog
      title="Remove invitation"
      description={`Are you sure you want to rescind the invitation to ${invite.email}?`}
      dialogContentProps={{
        onClick: (e) => e.stopPropagation(),
      }}
      customTrigger={
        <Button
          variant="outlineDestructive"
          size="icon"
          className="h-8 w-8"
          onClick={(e) => e.stopPropagation()}
        >
          <Trash size={16} />
        </Button>
      }
      dialogButtons={[
        <Button
          key="remove-invitation"
          variant="destructive"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            handleDelete();
          }}
        >
          Remove invitation
        </Button>,
        <Button variant="outline" key="remove-invitation-close">
          Close
        </Button>,
      ]}
    ></LilypadDialog>
  );
};

const AlternativeInviteLink = ({ inviteLink }: { inviteLink: string }) => {
  return (
    <>
      <div>Alternatively, give the invited user this link:</div>
      <div className="flex items-center space-x-2">
        <Input value={inviteLink} readOnly />
        <Button
          variant="outline"
          size="icon"
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            navigator.clipboard.writeText(inviteLink).catch(() => {
              toast.error("Failed to copy link");
            });
            toast.success("Copied link to clipboard");
          }}
        >
          <Copy />
        </Button>
      </div>
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
  const createOrganizationInvite = useCreateOrganizationInviteMutation();
  const onSubmit = async (data: OrganizationInviteCreate) => {
    const created = await createOrganizationInvite.mutateAsync(data);
    setOrganizationInvite(created);
    if (created.resend_email_id !== "n/a") {
      toast.success(`Successfully sent email invite to ${data.email}.`);
    }
  };
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="iconSm"
          className="text-primary hover:text-primary/80 hover:bg-white"
        >
          <PlusCircle />
        </Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <Form {...methods}>
          <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
            <DialogHeader className="flex-shrink-0">
              <DialogTitle>{`Invite user to ${organization.name}`}</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              An email will be sent to the user with an invitation to join the
              team.
            </DialogDescription>
            <FormField
              key="email"
              control={methods.control}
              name="email"
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
            {organizationInvite?.invite_link && (
              <AlternativeInviteLink
                inviteLink={organizationInvite.invite_link}
              />
            )}
            <DialogFooter>
              {!organizationInvite ? (
                <Button
                  type="submit"
                  loading={methods.formState.isSubmitting}
                  className="w-full"
                >
                  {methods.formState.isSubmitting
                    ? "Sending invite..."
                    : "Send invite"}
                </Button>
              ) : (
                <DialogClose asChild>
                  <Button
                    variant="outline"
                    onClick={() => setOrganizationInvite(null)}
                    className="w-full"
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
  const methods = useForm<UserOrganizationUpdate>({
    defaultValues: { role: userOrganization?.role },
  });
  const onSubmit = async (data: UserOrganizationUpdate) => {
    await updateUserOrganization
      .mutateAsync({
        userOrganizationUuid: userOrganization.uuid,
        data,
      })
      .catch(() => {
        toast.error("Failed to update user permissions");
      });
    toast.success("Successfully updated user permissions");
  };
  const roles = Object.values(UserRole).filter(
    (role) => role !== UserRole.OWNER
  );
  return (
    <div onClick={(e) => e.stopPropagation()}>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="outline" size="icon" className="h-8 w-8">
            <PencilLine />
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-[425px] overflow-x-auto">
          <Form {...methods}>
            <form
              onSubmit={methods.handleSubmit(onSubmit)}
              className="space-y-6"
            >
              <DialogHeader className="flex-shrink-0">
                <DialogTitle>{`Edit permissions for ${user.first_name}`}</DialogTitle>
              </DialogHeader>
              <DialogDescription>
                Update <b>{user.first_name}'s</b> role within the organization.
              </DialogDescription>
              <FormField
                key="role"
                control={methods.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <FormControl>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Change role" />
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
                    type="submit"
                    loading={methods.formState.isSubmitting}
                    className="w-full"
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
  const onSubmit = async () => {
    const successfullyDeleted = await deleteUserOrganization
      .mutateAsync(userOrganization.uuid)
      .catch(() => {
        toast.error("Failed to remove user. Please try again.");
      });
    if (successfullyDeleted) {
      toast.success("Successfully removed user from organization");
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        <Button variant="outlineDestructive" size="icon" className="h-8 w-8">
          <Trash />
        </Button>
      </DialogTrigger>
      <DialogContent
        className={"max-w-[425px] overflow-x-auto"}
        onClick={(e) => e.stopPropagation()}
      >
        <Form {...methods}>
          <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
            <DialogHeader className="flex-shrink-0">
              <DialogTitle>{`Remove ${user.first_name}`}</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              This action will remove <b>{user.first_name}</b> from{" "}
              <b>{userOrganization.organization.name}</b>
            </DialogDescription>
            <DialogFooter>
              <DialogClose asChild>
                <Button
                  type="submit"
                  variant="destructive"
                  loading={methods.formState.isSubmitting}
                  className="w-full"
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
