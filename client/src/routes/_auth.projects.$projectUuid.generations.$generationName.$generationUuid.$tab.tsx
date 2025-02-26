import { CodeSnippet } from "@/components/CodeSnippet";
import { GenerationSpans } from "@/components/GenerationSpans";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GenerationPublic, PromptPublic } from "@/types/types";
import {
  generationsByNameQueryOptions,
  useArchiveGenerationMutation,
  usePatchGenerationMutation,
} from "@/utils/generations";
import { promptsBySignature } from "@/utils/prompts";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import JsonView from "@uiw/react-json-view";
import ReactMarkdown from "react-markdown";

import CardSkeleton from "@/components/CardSkeleton";
import LilypadDialog from "@/components/LilypadDialog";
import { MetricCharts } from "@/components/MetricsCharts";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Typography } from "@/components/ui/typography";
import { GenerationAnnotations } from "@/ee/components/GenerationAnnotations";
import { GenerationTab } from "@/types/generations";
import { Trash } from "lucide-react";
import { JSX, Suspense } from "react";

type GenerationRouteParams = {
  projectUuid: string;
  generationName: string;
  generationUuid: string;
  tab: GenerationTab;
};
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/generations/$generationName/$generationUuid/$tab"
)({
  params: {
    stringify(params: GenerationRouteParams) {
      return {
        projectUuid: params.projectUuid,
        generationName: params.generationName,
        generationUuid: params.generationUuid,
        tab: params.tab,
      };
    },
    parse(raw: Record<string, string>): GenerationRouteParams {
      let tab = raw.tab;
      if (!Object.values(GenerationTab).includes(tab as GenerationTab)) {
        tab = GenerationTab.OVERVIEW;
      }
      return {
        projectUuid: raw.projectUuid,
        generationName: raw.generationName,
        generationUuid: raw.generationUuid,
        tab: tab as GenerationTab,
      };
    },
  },
  validateSearch: (search): search is { tab: GenerationTab } => {
    const tab = search.tab;
    return Object.values(GenerationTab).includes(tab as GenerationTab);
  },

  component: () => (
    <Suspense fallback={<div>Loading...</div>}>
      <GenerationWorkbench />
    </Suspense>
  ),
});

type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
};

const GenerationWorkbench = () => {
  const { projectUuid, generationName, generationUuid, tab } = useParams({
    from: Route.id,
  });
  const { data: generations } = useSuspenseQuery(
    generationsByNameQueryOptions(generationName, projectUuid)
  );

  const navigate = useNavigate();
  const generation = generations.find(
    (generation) => generation.uuid === generationUuid
  );
  if (!generation) {
    return <div>No generation found.</div>;
  }
  const archiveGeneration = useArchiveGenerationMutation();
  const tabs: Tab[] = [
    {
      label: "Overview",
      value: GenerationTab.OVERVIEW,
      component: <Generation generation={generation} />,
    },
    {
      label: "Traces",
      value: GenerationTab.TRACES,
      component: (
        <GenerationSpans
          projectUuid={projectUuid}
          generationUuid={generation?.uuid}
        />
      ),
    },
    {
      label: "Annotations",
      value: GenerationTab.ANNOTATIONS,
      component: (
        <GenerationAnnotations
          projectUuid={projectUuid}
          generationUuid={generation?.uuid}
        />
      ),
    },
  ];
  const handleArchive = async () => {
    if (!generation) return;
    await archiveGeneration.mutateAsync({
      projectUuid,
      generationUuid: generation.uuid,
      generationName,
    });
    navigate({ to: `/projects/${projectUuid}/generations` });
  };
  const tabWidth = 80 * tabs.length;
  return (
    <div className='w-full p-6'>
      <Typography variant='h2'>{generationName}</Typography>
      <div className='flex gap-2 items-center'>
        <Select
          value={generation?.uuid}
          onValueChange={(uuid) =>
            navigate({
              to: `/projects/${projectUuid}/generations/${generationName}/${uuid}/${tab}`,
            })
          }
        >
          <SelectTrigger className='w-[200px]'>
            <SelectValue placeholder='Select a generation' />
          </SelectTrigger>
          <SelectContent>
            {generations.map((generation) => (
              <SelectItem key={generation.uuid} value={generation.uuid}>
                v{generation.version_num}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {generation && (
          <LilypadDialog
            icon={<Trash />}
            title={`Delete ${generation.name} v${generation.version_num}`}
            description=''
            dialogContentProps={{
              className: "max-w-[600px]",
            }}
            buttonProps={{
              variant: "outlineDestructive",
              className: "w-9 h-9",
            }}
            dialogButtons={[
              <Button
                type='button'
                variant='destructive'
                onClick={handleArchive}
              >
                Delete
              </Button>,
              <Button type='button' variant='outline'>
                Cancel
              </Button>,
            ]}
          >
            {`Are you sure you want to delete ${generation.name} v${generation.version_num}?`}
          </LilypadDialog>
        )}
      </div>
      <Tabs defaultValue={tab} className='w-full'>
        <div className='flex justify-center w-full '>
          <TabsList className={`w-[${tabWidth}px]`}>
            {tabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>
        <Separator className='my-2' />
        <Suspense fallback={<div>Loading...</div>}>
          {tabs.map((tab) => (
            <TabsContent key={tab.value} value={tab.value} className='w-full'>
              {tab.component}
            </TabsContent>
          ))}
        </Suspense>
      </Tabs>
    </div>
  );
};

const PromptCard = ({
  prompt,
  generationUuid,
  activePromptUuid,
  index,
}: {
  prompt: PromptPublic;
  generationUuid: string;
  activePromptUuid?: string;
  index: number;
}) => {
  const { projectUuid } = useParams({ from: Route.id });
  const patchGeneration = usePatchGenerationMutation();
  const handleButtonClick = () => {
    patchGeneration.mutate({
      projectUuid,
      generationUuid,
      generationUpdate: { prompt_uuid: prompt.uuid },
    });
  };
  return (
    <Card className='w-auto'>
      <CardHeader>
        <CardTitle>{prompt.name}</CardTitle>
        <CardDescription>Version {index + 1}</CardDescription>
      </CardHeader>
      <CardContent className='flex flex-col gap-2 h-[200px] overflow-auto'>
        <Label>Template</Label>
        <ReactMarkdown>{prompt.template}</ReactMarkdown>
        <Separator />
        <Label>Call Parameters</Label>
        <JsonView value={prompt.call_params} />
      </CardContent>
      <CardFooter className='p-6'>
        <Button
          className='w-full'
          disabled={prompt.uuid === activePromptUuid}
          onClick={handleButtonClick}
        >
          {prompt.uuid === activePromptUuid ? "Active" : "Set active"}
        </Button>
      </CardFooter>
    </Card>
  );
};
const Generation = ({ generation }: { generation: GenerationPublic }) => {
  const { projectUuid } = useParams({ from: Route.id });

  const { data: prompts } = useSuspenseQuery(
    promptsBySignature(projectUuid, generation?.prompt?.signature)
  );

  if (!generation) {
    return <div>No generation selected.</div>;
  }
  return (
    <>
      {generation && (
        <div className='p-4 flex flex-col gap-2 max-w-4xl mx-auto'>
          <Suspense fallback={<CardSkeleton />}>
            <MetricCharts
              generationUuid={generation.uuid}
              projectUuid={projectUuid}
            />
          </Suspense>
          <div className='text-left'>
            <Label>Code</Label>
            <CodeSnippet code={generation.code} />
            <Label>Available Prompts</Label>
            <div className='flex gap-4 w-max-full flex-wrap'>
              {prompts.map((prompt, i) => (
                <PromptCard
                  key={prompt.uuid}
                  generationUuid={generation.uuid}
                  activePromptUuid={generation.prompt?.uuid}
                  prompt={prompt}
                  index={i}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
