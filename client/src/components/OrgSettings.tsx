import { APIKeysTable } from "@/components/APIKeysTable";
import { EnvironmentsTable } from "@/components/EnvironmentsTable";
import { NotFound } from "@/components/NotFound";
import { ProjectsTable } from "@/components/ProjectsTable";
import { UserOrgTable } from "@/components/UserOrgTable";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";

export const OrgSettings = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const activeUserOrg = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  if (!activeUserOrg) return <NotFound />;
  return (
    <>
      <UserOrgTable />
      <ProjectsTable />
      <EnvironmentsTable />
      <APIKeysTable />
    </>
  );
};
