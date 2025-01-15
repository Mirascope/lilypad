import { HomeSettings } from "@/components/HomeSettings";
import { KeysSettings } from "@/components/KeysSettings";
import { OrgSettings } from "@/components/OrgSettings";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
export const Route = createFileRoute("/_auth/settings/$")({
  component: () => <Settings />,
});
type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
};

const Settings = () => {
  const navigate = useNavigate();
  const params = useParams({
    from: Route.id,
  });
  let { _splat: tab } = params;
  const tabs: Tab[] = [
    {
      label: "Overview",
      value: "overview",
      component: <HomeSettings />,
    },
    {
      label: "LLM Keys",
      value: "keys",
      component: <KeysSettings />,
    },
    {
      label: "Organization",
      value: "org",
      component: <OrgSettings />,
    },
  ];
  if (tab && !tabs.some((t) => t.value === tab)) {
    tab = "overview";
  }
  const activeTab = tab || "overview";

  const handleTabChange = (value: string) => {
    navigate({
      to: `/settings/${value}`,
      replace: true,
    });
  };
  const tabWidth = 90 * tabs.length;

  return (
    <Tabs
      value={activeTab}
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
      {tabs.map((tab) => (
        <TabsContent
          key={tab.value}
          value={tab.value}
          className='w-full bg-gray-50 h-full'
        >
          {tab.component}
        </TabsContent>
      ))}
    </Tabs>
  );
};
