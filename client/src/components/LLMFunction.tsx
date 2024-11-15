import { Evaluate } from "@/components/Evaluate";
import { Playground } from "@/components/Playground";
import { TracesTable } from "@/components/TracesTable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { VersionPublic } from "@/types/types";
type LLMFunctionProps = {
  projectId: number;
  version: VersionPublic | null;
};

export const LLMFunction = ({ projectId, version }: LLMFunctionProps) => {
  return (
    <div className='w-full'>
      <Tabs defaultValue='prompt' className='w-full'>
        <div className='flex justify-center w-full'>
          <TabsList className='w-[240px]'>
            <TabsTrigger value='prompt'>Prompt</TabsTrigger>
            <TabsTrigger value='evaluate'>Evaluate</TabsTrigger>
            <TabsTrigger value='traces'>Traces</TabsTrigger>
          </TabsList>
        </div>
        <TabsContent value='prompt' className='w-full bg-gray-50'>
          {version && projectId && (
            <Playground version={version} projectId={Number(projectId)} />
          )}
        </TabsContent>
        <TabsContent value='evaluate' className='w-full bg-gray-50'>
          {version && projectId && (
            <Evaluate version={version} projectId={Number(projectId)} />
          )}
        </TabsContent>
        <TabsContent value='traces' className='w-full bg-gray-50'>
          {version && projectId && <TracesTable data={version.spans} />}
        </TabsContent>
      </Tabs>
    </div>
  );
};
