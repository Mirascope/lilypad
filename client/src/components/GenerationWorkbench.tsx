import { GenerationSpans } from "@/components/GenerationSpans";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { GenerationPublic } from "@/types/types";
type LLMFunctionProps = {
  projectUuid: string;
  generationVersion: GenerationPublic | null;
};

type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
};
export const GenerationWorkbench = ({
  projectUuid,
  generationVersion,
}: LLMFunctionProps) => {
  const tabs: Tab[] = [
    {
      label: "Traces",
      value: "traces",
      component: generationVersion && (
        <GenerationSpans
          projectUuid={projectUuid}
          generationUuid={generationVersion.uuid}
        />
      ),
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
