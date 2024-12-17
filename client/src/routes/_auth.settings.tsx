import { createFileRoute } from "@tanstack/react-router";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { KeysSettings } from "@/components/KeysSettings";
import { HomeSettings } from "@/components/HomeSettings";
export const Route = createFileRoute("/_auth/settings")({
  component: () => <Settings />,
});
type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
};
const Settings = () => {
  const tabs: Tab[] = [
    {
      label: "Overview",
      value: "overview",
      component: <HomeSettings />,
    },
    {
      label: "Keys",
      value: "keys",
      component: <KeysSettings />,
    },
  ];
  const tabWidth = 80 * tabs.length;
  return (
    <Tabs defaultValue='overview' className='flex flex-col h-full'>
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
