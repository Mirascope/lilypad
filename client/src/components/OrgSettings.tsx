import { APIKeysTable } from "@/components/APIKeysTable";
import { NotFound } from "@/components/NotFound";
import { ProjectsTable } from "@/components/ProjectsTable";
import { SettingsLayout } from "@/components/SettingsLayout";
import { UserOrgTable } from "@/components/UserOrgTable";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { KeyRound } from "lucide-react";
import { Suspense } from "react";

export const OrgSettings = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const activeUserOrg = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  if (!activeUserOrg) return <NotFound />;
  return (
    <SettingsLayout
      title={`${activeUserOrg.organization.name}'s Settings`}
      icon={KeyRound}
    >
      <Suspense fallback={<div>Loading...</div>}>
        <UserOrgTable />
        <ProjectsTable />
        <APIKeysTable />
      </Suspense>
    </SettingsLayout>
  );
};
