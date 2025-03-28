import { HomeSettings } from "@/components/HomeSettings";
import { KeysSettings } from "@/components/KeysSettings";
import { LilypadLoading } from "@/components/LilypadLoading";
import { OrgSettings } from "@/components/OrgSettings";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { JSX, Suspense, useEffect } from "react";
export const Route = createFileRoute("/_auth/settings/$")({
  component: () => <Settings />,
});
interface Tab {
  label: string;
  value: string;
  component?: JSX.Element | null;
}

const Settings = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
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
      component: (
        <Suspense fallback={<LilypadLoading />}>
          <OrgSettings />
        </Suspense>
      ),
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
            {tab.component}
          </TabsContent>
        ))}
      </div>
    </Tabs>
  );
};
