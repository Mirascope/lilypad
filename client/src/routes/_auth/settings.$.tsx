import { HomeSettings } from "@/components/HomeSettings";
import { KeysSettings } from "@/components/KeysSettings";
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
  Pencil,
  SettingsIcon,
  Tag,
} from "lucide-react";
import { JSX, ReactNode, Suspense, useEffect, useState } from "react";
export const Route = createFileRoute("/_auth/settings/$")({
  component: () => <Settings />,
});
interface Tab {
  label: string;
  value: string;
  component: JSX.Element;
  title: string | ReactNode;
  icon: LucideIcon;
  disabled?: boolean;
}

const Settings = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const params = useParams({
    from: Route.id,
  });
  let { _splat: tab } = params;

  const activeUserOrg = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  const [open, setOpen] = useState<boolean>(false);
  const [isHovered, setIsHovered] = useState<boolean>(false);

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
            <div className="flex flex-col gap-10">
              <TableSkeleton rows={2} columns={3} />
              <TableSkeleton rows={2} columns={2} />
              <TableSkeleton rows={2} columns={3} />
              <TableSkeleton rows={2} columns={6} />
            </div>
          }
        >
          <OrgSettings open={open} setOpen={setOpen} />
        </Suspense>
      ),
      title: (
        <div
          className="flex items-center gap-2 cursor-pointer"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <h1 className="text-xl font-semibold">
            {activeUserOrg?.organization.name}&apos;s Settings
          </h1>
          {isHovered && (
            <Pencil
              className="h-4 w-4 text-gray-500"
              onClick={() => setOpen(true)}
            />
          )}
        </div>
      ),
      icon: Building2,
      disabled: !activeUserOrg,
    },
    {
      label: "Tags",
      value: "tags",
      component: (
        <Suspense fallback={<TableSkeleton />}>
          <TagsTable />
        </Suspense>
      ),
      title: `${activeUserOrg?.organization.name}'s Tags`,
      icon: Tag,
      disabled: !activeUserOrg,
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
      className="flex flex-col h-full"
    >
      <div className="flex justify-center w-full">
        <TabsList className={`w-[${tabWidth}px]`}>
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              disabled={tab.disabled}
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      <div className="flex-1 min-h-0 relative">
        {tabs.map((tab) => (
          <TabsContent
            key={tab.value}
            value={tab.value}
            className="w-full bg-gray-50 absolute inset-0 overflow-auto"
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
