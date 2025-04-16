import { HomeSettings } from "@/components/HomeSettings";
import { KeysSettings } from "@/components/KeysSettings";
import { NotFound } from "@/components/NotFound";
import { OrgSettings } from "@/components/OrgSettings";
import { SettingsLayout } from "@/components/SettingsLayout";
import TableSkeleton from "@/components/TableSkeleton";
import { TagsTable } from "@/components/TagsTable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import {
  Building2,
  KeyRound,
  LucideIcon,
  SettingsIcon,
  Tag,
} from "lucide-react";
import { JSX, Suspense, useEffect } from "react";
export const Route = createFileRoute("/_auth/settings/$")({
  component: () => <Settings />,
});
interface Tab {
  label: string;
  value: string;
  component: JSX.Element;
  title: string;
  icon: LucideIcon;
}

const Settings = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const activeUserOrg = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  const params = useParams({
    from: Route.id,
  });
  if (!activeUserOrg) return <NotFound />;
  let { _splat: tab } = params;
  const tabs: Tab[] = [
    {
      label: "Overview",
      value: "overview",
      component: (
        <Suspense fallback={<TableSkeleton />}>
          <HomeSettings />
        </Suspense>
      ),
      title: "Overview",
      icon: SettingsIcon,
    },
    {
      label: "LLM Keys",
      value: "keys",
      component: (
        <Suspense fallback={<TableSkeleton />}>
          <KeysSettings />
        </Suspense>
      ),
      title: `${user.first_name}'s Keys`,
      icon: KeyRound,
    },
    {
      label: "Organization",
      value: "org",
      component: (
        <Suspense
          fallback={
            <div className='flex flex-col gap-10'>
              <TableSkeleton rows={2} columns={3} />
              <TableSkeleton rows={2} columns={2} />
              <TableSkeleton rows={2} columns={3} />
              <TableSkeleton rows={2} columns={6} />
            </div>
          }
        >
          <OrgSettings />
        </Suspense>
      ),
      title: `${activeUserOrg.organization.name}'s Settings`,
      icon: Building2,
    },
    {
      label: "Tags",
      value: "tags",
      component: (
        <Suspense fallback={<TableSkeleton />}>
          <TagsTable />
        </Suspense>
      ),
      title: `${activeUserOrg.organization.name}'s Tags`,
      icon: Tag,
    },
  ];
  useEffect(() => {
    if (tab) {
      navigate({
        to: `/settings/${tab}`,
        replace: true,
      }).catch(() =>
        toast({
          title: "Navigation failed",
        })
      );
    } else {
      navigate({
        to: `/settings/$`,
        params: { _splat: "overview" },
        replace: true,
      }).catch(() =>
        toast({
          title: "Navigation failed",
        })
      );
    }
  }, [tab, navigate, toast]);
  if (tab && !tabs.some((t) => t.value === tab)) {
    tab = "overview";
  }
  const handleTabChange = (value: string) => {
    navigate({
      to: `/settings/$`,
      params: { _splat: value },
      replace: true,
    }).catch(() =>
      toast({
        title: "Navigation failed",
      })
    );
  };
  const tabWidth = 90 * tabs.length;

  return (
    <Tabs
      value={tab ?? "overview"}
      onValueChange={handleTabChange}
      className='flex flex-col h-full'
    >
      <div className='flex justify-center w-full'>
        <TabsList className={`w-[${tabWidth}px]`}>
          {tabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      <div className='flex-1 min-h-0 relative'>
        {tabs.map((tab) => (
          <TabsContent
            key={tab.value}
            value={tab.value}
            className='w-full bg-gray-50 absolute inset-0 overflow-auto'
          >
            <SettingsLayout title={tab.title} icon={tab.icon}>
              {tab.component}
            </SettingsLayout>
          </TabsContent>
        ))}
      </div>
    </Tabs>
  );
};
