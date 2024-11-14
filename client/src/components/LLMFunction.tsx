import { Evaluate } from "@/components/Evaluate";
import { Playground } from "@/components/Playground";
import { TracesTable } from "@/components/TracesTable";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { VersionPublic } from "@/types/types";
import { projectQueryOptions } from "@/utils/projects";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useEffect } from "react";
import {
  Controller,
  FormProvider,
  useForm,
  useFormState,
  useWatch,
} from "react-hook-form";

type LLMFunctionForm = {
  functionName: string;
  version: VersionPublic | null;
};

type LLMFunctionProps = {
  projectId: number;
  versions: VersionPublic[];
  defaultFunctionName?: string;
  versionId?: number;
};

export const LLMFunction = ({
  projectId,
  versions,
  defaultFunctionName,
  versionId,
}: LLMFunctionProps) => {
  const navigate = useNavigate();
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectId));
  console.log(versions);
  const defaultVersion = versionId
    ? versions.find((v) => v.id == versionId)
    : null;
  const method = useForm<LLMFunctionForm>({
    defaultValues: {
      functionName: defaultFunctionName,
      version: defaultVersion,
    },
  });
  const { dirtyFields } = useFormState({
    control: method.control,
  });
  const functionName = useWatch({
    control: method.control,
    name: "functionName",
  });
  const version = useWatch({
    control: method.control,
    name: "version",
  });
  useEffect(() => {
    if (dirtyFields.functionName) {
      method.resetField("version", undefined);
    }
  }, [functionName, dirtyFields]);

  const uniqueFunctionNames = Array.from(
    new Set(project?.functions?.map((fn) => fn.name) ?? [])
  );
  if (functionName && !versions) return <div>No versions found</div>;
  return (
    <div className='w-full'>
      <FormProvider {...method}>
        <div className='flex gap-2'>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                size='icon'
                onClick={() =>
                  navigate({ to: `/projects/${projectId}/functions` })
                }
              >
                <Plus />
              </Button>
            </TooltipTrigger>
            <TooltipContent className='bg-slate-500'>
              <p>Create a new function</p>
            </TooltipContent>
          </Tooltip>
          <Controller
            control={method.control}
            name='functionName'
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger className='w-[200px]'>
                  <SelectValue placeholder='Select a function' />
                </SelectTrigger>
                <SelectContent>
                  {uniqueFunctionNames.map((name) => (
                    <SelectItem key={name} value={name}>
                      {name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          <Controller
            control={method.control}
            name='version'
            render={({ field }) => (
              <Select
                value={JSON.stringify(field.value)}
                onValueChange={(value) => field.onChange(JSON.parse(value))}
                disabled={!functionName || !versions}
              >
                <SelectTrigger className='w-[100px]'>
                  <SelectValue placeholder='version' />
                </SelectTrigger>
                <SelectContent>
                  {versions?.map((version, i) => (
                    <SelectItem
                      key={version.id}
                      value={JSON.stringify(version)}
                    >
                      v{i + 1}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </FormProvider>
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
