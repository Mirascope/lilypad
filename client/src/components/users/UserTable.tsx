import { DataTable } from "@/components/DataTable";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { CancelInviteUserDialog } from "@/components/users/CancelInviteUserDialog";
import { EditUserPermissionsDialog } from "@/components/users/EditUserPermissionsDialog";
import { InviteUserDialog } from "@/components/users/InviteUserDialog";
import { RemoveUserDialog } from "@/components/users/RemoveUserDialog";
import { ResendInviteUserDialog } from "@/components/users/ResendInviteUserDialog";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { OrganizationInvitePublic, UserPublic, UserRole } from "@/types/types";
import { organizationInvitesQueryOptions } from "@/utils/organizations";
import {
  userQueryOptions,
  usersByOrganizationQueryOptions,
} from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ColumnDef } from "@tanstack/react-table";
import { Mail } from "lucide-react";
import { useRef, useState } from "react";

type UserData = UserPublic | ({ isInvite: true } & OrganizationInvitePublic);

export const UserTable = () => {
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
      size: 200,
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
              <CancelInviteUserDialog invite={rowData} />
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
          <InviteUserDialog
            title={`Invite user to ${userOrganization.organization.name}`}
            description="An email will be sent to the user with an invitation to join the
              team."
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
        <ResendInviteUserDialog
          invite={activeInvite}
          open={resendInviteOpen}
          setOpen={setResendInviteOpen}
          onClose={() => setActiveInvite(null)}
        />
      )}
    </>
  );
};
