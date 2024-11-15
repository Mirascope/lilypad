import { CreateEditorForm } from "@/components/CreateEditorForm";
import { FunctionSpans } from "@/components/FunctionSpans";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { VersionPublic } from "@/types/types";
type LLMFunctionProps = {
  projectId: number;
  version: VersionPublic | null;
};

type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
};
export const LLMFunction = ({ projectId, version }: LLMFunctionProps) => {
  const tabs: Tab[] = [
    {
      label: "Prompt",
      value: "prompt",
      component: (projectId && <CreateEditorForm version={version} />) || null,
    },
    {
      label: "Traces",
      value: "traces",
      component: version && <FunctionSpans />,
    },
  ];
  const tabWidth = 80 * tabs.length;
  return (
    <div className='w-full'>
      <Tabs defaultValue='prompt' className='w-full'>
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
            className='w-full bg-gray-50'
          >
            {tab.component}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
};
