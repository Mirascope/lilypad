import { HomeSettings } from "@/src/components/HomeSettings";
import { KeysSettings } from "@/src/components/KeysSettings";
import { OrgSettings } from "@/src/components/OrgSettings";
import { SubscriptionManager } from "@/src/components/stripe/SubscriptionManager";
import { Tab, TabGroup } from "@/src/components/TabGroup";
import TableSkeleton from "@/src/components/TableSkeleton";
import { TagsTable } from "@/src/components/TagsTable";
import { Typography } from "@/src/components/ui/typography";
import { userQueryOptions } from "@/src/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router";
import { Building2, CreditCard, KeyRound, SettingsIcon, Tag } from "lucide-react";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";
export const Route = createFileRoute("/_auth/settings/$")({
  component: () => <Settings />,
});

const Settings = () => {
  const navigate = useNavigate();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const params = useParams({
    from: Route.id,
  });
  let { _splat: tab } = params;

  const activeUserOrg = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  const [open, setOpen] = useState<boolean>(false);

  const tabs: Tab[] = [
    {
      label: (
        <div className="flex items-center gap-1">
          <SettingsIcon />
          <span>Overview</span>
        </div>
      ),
      value: "overview",
      component: (
        <Suspense fallback={<TableSkeleton />}>
          <div className="p-2">
            <HomeSettings />
          </div>
        </Suspense>
      ),
    },
    {
      label: (
        <div className="flex items-center gap-1">
          <KeyRound />
          <span>LLM Keys</span>
        </div>
      ),
      value: "keys",
      component: (
        <Suspense fallback={<TableSkeleton />}>
          <div className="p-2">
            <KeysSettings />
          </div>
        </Suspense>
      ),
    },
    {
      label: (
        <div className="flex items-center gap-1">
          <Building2 />
          <span>Organization</span>
        </div>
      ),
      value: "org",
      component: activeUserOrg ? (
        <Suspense
          fallback={
            <div className="flex flex-col gap-10">
              <TableSkeleton rows={2} columns={3} />
              <TableSkeleton rows={2} columns={2} />
              <TableSkeleton rows={2} columns={3} />
              <TableSkeleton rows={2} columns={6} />
            </div>
          }
        >
          <div className="p-2">
            <OrgSettings open={open} setOpen={setOpen} />
          </div>
        </Suspense>
      ) : null,
    },
    {
      label: (
        <div className="flex items-center gap-1">
          <CreditCard />
          <span>Billing</span>
        </div>
      ),
      value: "billing",
      component: activeUserOrg ? (
        <Suspense fallback={<TableSkeleton />}>
          <div className="p-2">
            <SubscriptionManager />
          </div>
        </Suspense>
      ) : null,
    },
    {
      label: (
        <div className="flex items-center gap-1">
          <Tag />
          <span>Tags</span>
        </div>
      ),
      value: "tags",
      component: activeUserOrg ? (
        <Suspense fallback={<TableSkeleton />}>
          <div className="p-2">
            <TagsTable />
          </div>
        </Suspense>
      ) : null,
    },
  ];
  if (tab && !tabs.some((t) => t.value === tab)) {
    tab = "overview";
  }
  useEffect(() => {
    if (tab) {
      navigate({
        to: `/settings/${tab}`,
        replace: true,
      }).catch(() => toast.error("Failed to navigate to settings page."));
    } else {
      navigate({
        to: `/settings/$`,
        params: { _splat: "overview" },
        replace: true,
      }).catch(() => toast.error("Failed to navigate to settings page."));
    }
  }, [tab, navigate, toast]);
  const handleTabChange = (value: string) => {
    navigate({
      to: `/settings/$`,
      params: { _splat: value },
      replace: true,
    }).catch(() => toast.error("Failed to navigate to settings page."));
  };
  return (
    <div className="flex flex-col gap-2 p-2">
      <Typography variant="h3">Settings</Typography>
      <TabGroup tabs={tabs} tab={tab} handleTabChange={handleTabChange} />
    </div>
  );
};
